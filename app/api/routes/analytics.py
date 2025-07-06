"""
Traditional analytics endpoints for hotel review data.
Provides classical REST-based analytics and aggregation endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Request
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from loguru import logger

from app.core.schema_gremlin_client import SchemaAwareGremlinClient
from app.models.dto import ErrorResponse


router = APIRouter(prefix="/api/v1", tags=["analytics"])


# Request/Response Models for Analytics
class DateRangeFilter(BaseModel):
    """Date range filter for analytics queries."""
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")


class ReviewFilters(BaseModel):
    """Filters for review queries."""
    language: Optional[str] = Field(None, description="Review language (e.g., 'en', 'es')")
    source: Optional[str] = Field(None, description="Review source (e.g., 'TripAdvisor', 'Booking.com')")
    aspect: Optional[str] = Field(None, description="Aspect category (e.g., 'cleanliness', 'service')")
    sentiment: Optional[str] = Field(None, description="Sentiment category (e.g., 'positive', 'negative')")
    hotel: Optional[str] = Field(None, description="Hotel name or ID")
    date_range: Optional[DateRangeFilter] = Field(None, description="Date range filter")
    min_rating: Optional[float] = Field(None, ge=0, le=10, description="Minimum rating")
    max_rating: Optional[float] = Field(None, ge=0, le=10, description="Maximum rating")


class GroupStats(BaseModel):
    """Statistics for hotel groups."""
    group_id: str
    group_name: str
    hotel_count: int
    total_reviews: int
    average_rating: float
    review_sources: List[str]
    top_aspects: List[Dict[str, Any]]


class HotelStats(BaseModel):
    """Statistics for individual hotels."""
    hotel_id: str
    hotel_name: str
    group_name: Optional[str]
    total_reviews: int
    average_rating: float
    aspect_scores: Dict[str, float]
    language_distribution: Dict[str, int]
    source_distribution: Dict[str, int]
    accommodation_types: List[str]


class AspectBreakdown(BaseModel):
    """Aspect-level breakdown for a hotel."""
    aspect_name: str
    average_score: float
    review_count: int
    positive_percentage: float
    negative_percentage: float
    trending: str  # "up", "down", "stable"


class ReviewResponse(BaseModel):
    """Response model for review queries."""
    reviews: List[Dict[str, Any]]
    total_count: int
    filters_applied: ReviewFilters
    aggregations: Dict[str, Any]


def get_gremlin_client(request: Request) -> SchemaAwareGremlinClient:
    """Dependency to get Gremlin client from app state."""
    return getattr(request.app.state, 'gremlin_client', None)


# SECTION 1: Traditional Analytics Endpoints

@router.get("/average/groups", response_model=List[GroupStats])
async def get_group_statistics(
    gremlin_client: SchemaAwareGremlinClient = Depends(get_gremlin_client)
):
    """
    Get group-level statistics and averages.
    
    Returns aggregated data for all hotel groups including:
    - Hotel count per group
    - Average ratings across hotels
    - Review volume and sources
    - Top performing aspects
    """
    if not gremlin_client or not gremlin_client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Graph database not available"
        )
    
    try:
        # Query hotel groups with aggregated statistics
        query = """
        g.V().hasLabel('HotelGroup').as('group')
         .project('group_id', 'group_name', 'hotel_count', 'total_reviews', 'average_rating', 'review_sources', 'top_aspects')
         .by(__.values('id'))
         .by(__.values('name'))
         .by(__.out('OWNS').count())
         .by(__.out('OWNS').in('BELONGS_TO').in('HAS_REVIEW').count())
         .by(__.out('OWNS').in('BELONGS_TO').in('HAS_REVIEW').values('overall_score').mean())
         .by(__.out('OWNS').in('BELONGS_TO').in('HAS_REVIEW').out('FROM_SOURCE').values('name').dedup().fold())
         .by(__.out('OWNS').in('BELONGS_TO').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').groupCount().by(__.values('name')).unfold().order().by(__.select(values), desc).limit(5).fold())
        """
        
        results = await gremlin_client.execute_query(query)
        
        group_stats = []
        for result in results:
            stats = GroupStats(
                group_id=result.get('group_id', ''),
                group_name=result.get('group_name', ''),
                hotel_count=result.get('hotel_count', 0),
                total_reviews=result.get('total_reviews', 0),
                average_rating=round(result.get('average_rating', 0.0), 2),
                review_sources=result.get('review_sources', []),
                top_aspects=[
                    {"aspect": k, "count": v} 
                    for k, v in (result.get('top_aspects', {}) or {}).items()
                ]
            )
            group_stats.append(stats)
        
        return group_stats
        
    except Exception as e:
        logger.error(f"Error getting group statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve group statistics: {str(e)}"
        )


@router.get("/average/hotels", response_model=List[HotelStats])
async def get_hotel_statistics(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of hotels to return"),
    offset: int = Query(0, ge=0, description="Number of hotels to skip"),
    group_name: Optional[str] = Query(None, description="Filter by hotel group name"),
    min_rating: Optional[float] = Query(None, ge=0, le=10, description="Minimum average rating"),
    gremlin_client: SchemaAwareGremlinClient = Depends(get_gremlin_client)
):
    """
    Get hotel-level statistics and averages.
    
    Returns comprehensive statistics for hotels including:
    - Review volume and average ratings
    - Aspect-specific scores
    - Language and source distributions
    - Accommodation type information
    """
    if not gremlin_client or not gremlin_client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Graph database not available"
        )
    
    try:
        # Build dynamic query based on filters
        base_query = "g.V().hasLabel('Hotel')"
        
        if group_name:
            base_query += f".where(__.out('BELONGS_TO').has('name', '{group_name}'))"
        
        query = f"""
        {base_query}.as('hotel')
         .project('hotel_id', 'hotel_name', 'group_name', 'total_reviews', 'average_rating', 'aspect_scores', 'language_distribution', 'source_distribution', 'accommodation_types')
         .by(__.values('id'))
         .by(__.values('name'))
         .by(__.out('BELONGS_TO').values('name').fold())
         .by(__.in('BELONGS_TO').in('HAS_REVIEW').count())
         .by(__.in('BELONGS_TO').in('HAS_REVIEW').values('overall_score').mean())
         .by(__.in('BELONGS_TO').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').group().by(__.values('name')).by(__.in('ANALYZES_ASPECT').values('aspect_score').mean()))
         .by(__.in('BELONGS_TO').in('HAS_REVIEW').out('WRITTEN_IN').groupCount().by(__.values('code')))
         .by(__.in('BELONGS_TO').in('HAS_REVIEW').out('FROM_SOURCE').groupCount().by(__.values('name')))
         .by(__.out('OFFERS').values('type').dedup().fold())
         .range({offset}, {offset + limit})
        """
        
        results = await gremlin_client.execute_query(query)
        
        hotel_stats = []
        for result in results:
            # Apply rating filter if specified
            avg_rating = result.get('average_rating', 0.0)
            if min_rating and avg_rating < min_rating:
                continue
                
            stats = HotelStats(
                hotel_id=result.get('hotel_id', ''),
                hotel_name=result.get('hotel_name', ''),
                group_name=result.get('group_name', [None])[0] if result.get('group_name') else None,
                total_reviews=result.get('total_reviews', 0),
                average_rating=round(avg_rating, 2),
                aspect_scores={
                    k: round(v, 2) for k, v in (result.get('aspect_scores', {}) or {}).items()
                },
                language_distribution=result.get('language_distribution', {}),
                source_distribution=result.get('source_distribution', {}),
                accommodation_types=result.get('accommodation_types', [])
            )
            hotel_stats.append(stats)
        
        return hotel_stats
        
    except Exception as e:
        logger.error(f"Error getting hotel statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve hotel statistics: {str(e)}"
        )


@router.get("/average/{hotel_name}", response_model=Dict[str, Any])
async def get_hotel_averages(
    hotel_name: str = Path(..., description="Hotel name"),
    gremlin_client: SchemaAwareGremlinClient = Depends(get_gremlin_client)
):
    """
    Get aspect and category averages for a specific hotel.
    
    Returns detailed breakdown of:
    - Overall rating
    - Aspect-specific scores (cleanliness, service, location, etc.)
    - Category averages
    - Sentiment distribution
    - Trend analysis
    """
    if not gremlin_client or not gremlin_client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Graph database not available"
        )
    
    try:
        # Get hotel with detailed aspect breakdown
        query = f"""
        g.V().hasLabel('Hotel').has('name', '{hotel_name}').as('hotel')
         .project('hotel_info', 'overall_stats', 'aspect_breakdown', 'sentiment_distribution', 'recent_trends')
         .by(__.project('id', 'name', 'group').by(__.values('id')).by(__.values('name')).by(__.out('BELONGS_TO').values('name').fold()))
         .by(__.project('total_reviews', 'average_rating', 'rating_distribution')
             .by(__.in('BELONGS_TO').in('HAS_REVIEW').count())
             .by(__.in('BELONGS_TO').in('HAS_REVIEW').values('overall_score').mean())
             .by(__.in('BELONGS_TO').in('HAS_REVIEW').groupCount().by(__.values('overall_score'))))
         .by(__.in('BELONGS_TO').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').group()
             .by(__.values('name'))
             .by(__.project('average_score', 'review_count', 'sentiment_breakdown')
                 .by(__.in('ANALYZES_ASPECT').values('aspect_score').mean())
                 .by(__.in('ANALYZES_ASPECT').count())
                 .by(__.in('ANALYZES_ASPECT').groupCount().by(__.values('sentiment')))))
         .by(__.in('BELONGS_TO').in('HAS_REVIEW').in('HAS_ANALYSIS').groupCount().by(__.values('overall_sentiment')))
         .by(__.in('BELONGS_TO').in('HAS_REVIEW').has('date', gte('2024-01-01')).groupCount().by(__.values('date').map({{it.get().toString().substring(0,7)}})))
        """
        
        results = await gremlin_client.execute_query(query)
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"Hotel '{hotel_name}' not found"
            )
        
        result = results[0]
        
        # Process aspect breakdown
        aspect_breakdown = []
        aspects_data = result.get('aspect_breakdown', {})
        for aspect_name, aspect_data in aspects_data.items():
            sentiment_breakdown = aspect_data.get('sentiment_breakdown', {})
            total_sentiment_reviews = sum(sentiment_breakdown.values())
            
            breakdown = AspectBreakdown(
                aspect_name=aspect_name,
                average_score=round(aspect_data.get('average_score', 0.0), 2),
                review_count=aspect_data.get('review_count', 0),
                positive_percentage=round(
                    (sentiment_breakdown.get('positive', 0) / max(total_sentiment_reviews, 1)) * 100, 1
                ),
                negative_percentage=round(
                    (sentiment_breakdown.get('negative', 0) / max(total_sentiment_reviews, 1)) * 100, 1
                ),
                trending="stable"  # TODO: Calculate based on time series data
            )
            aspect_breakdown.append(breakdown)
        
        response = {
            "hotel_info": result.get('hotel_info', {}),
            "overall_stats": result.get('overall_stats', {}),
            "aspect_breakdown": [aspect.dict() for aspect in aspect_breakdown],
            "sentiment_distribution": result.get('sentiment_distribution', {}),
            "recent_trends": result.get('recent_trends', {}),
            "generated_at": datetime.now().isoformat()
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hotel averages for {hotel_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve hotel averages: {str(e)}"
        )


@router.get("/average/{hotel_id}/languages", response_model=Dict[str, Any])
async def get_hotel_language_distribution(
    hotel_id: str = Path(..., description="Hotel ID"),
    gremlin_client: SchemaAwareGremlinClient = Depends(get_gremlin_client)
):
    """
    Get language distribution for reviews of a specific hotel.
    
    Returns:
    - Language codes with review counts
    - Percentage breakdown
    - Average ratings per language
    - Recent language trends
    """
    if not gremlin_client or not gremlin_client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Graph database not available"
        )
    
    try:
        query = f"""
        g.V().hasLabel('Hotel').has('id', '{hotel_id}').as('hotel')
         .project('hotel_name', 'language_stats', 'language_ratings', 'total_reviews')
         .by(__.values('name'))
         .by(__.in('BELONGS_TO').in('HAS_REVIEW').out('WRITTEN_IN').group()
             .by(__.project('code', 'name').by(__.values('code')).by(__.values('name')))
             .by(__.in('WRITTEN_IN').count()))
         .by(__.in('BELONGS_TO').in('HAS_REVIEW').out('WRITTEN_IN').group()
             .by(__.values('code'))
             .by(__.in('WRITTEN_IN').values('overall_score').mean()))
         .by(__.in('BELONGS_TO').in('HAS_REVIEW').count())
        """
        
        results = await gremlin_client.execute_query(query)
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"Hotel with ID '{hotel_id}' not found"
            )
        
        result = results[0]
        total_reviews = result.get('total_reviews', 0)
        language_stats = result.get('language_stats', {})
        language_ratings = result.get('language_ratings', {})
        
        # Process language distribution
        distribution = []
        for lang_info, count in language_stats.items():
            if isinstance(lang_info, dict):
                lang_code = lang_info.get('code', 'unknown')
                lang_name = lang_info.get('name', 'Unknown')
            else:
                lang_code = str(lang_info)
                lang_name = lang_code
            
            percentage = round((count / max(total_reviews, 1)) * 100, 1)
            avg_rating = language_ratings.get(lang_code, 0.0)
            
            distribution.append({
                "language_code": lang_code,
                "language_name": lang_name,
                "review_count": count,
                "percentage": percentage,
                "average_rating": round(avg_rating, 2)
            })
        
        # Sort by review count
        distribution.sort(key=lambda x: x["review_count"], reverse=True)
        
        response = {
            "hotel_id": hotel_id,
            "hotel_name": result.get('hotel_name', ''),
            "total_reviews": total_reviews,
            "language_distribution": distribution,
            "top_languages": distribution[:5],
            "language_diversity_score": len(distribution),
            "generated_at": datetime.now().isoformat()
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting language distribution for hotel {hotel_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve language distribution: {str(e)}"
        )


@router.get("/average/{hotel_name}/sources", response_model=Dict[str, Any])
async def get_hotel_source_distribution(
    hotel_name: str = Path(..., description="Hotel name"),
    gremlin_client: SchemaAwareGremlinClient = Depends(get_gremlin_client)
):
    """
    Get review source distribution for a specific hotel.
    
    Returns breakdown by review sources like:
    - TripAdvisor, Booking.com, Hotels.com, etc.
    - Review counts and percentages per source
    - Average ratings per source
    - Source reliability metrics
    """
    if not gremlin_client or not gremlin_client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Graph database not available"
        )
    
    try:
        query = f"""
        g.V().hasLabel('Hotel').has('name', '{hotel_name}').as('hotel')
         .project('hotel_id', 'source_stats', 'source_ratings', 'source_details', 'total_reviews')
         .by(__.values('id'))
         .by(__.in('BELONGS_TO').in('HAS_REVIEW').out('FROM_SOURCE').groupCount().by(__.values('name')))
         .by(__.in('BELONGS_TO').in('HAS_REVIEW').out('FROM_SOURCE').group()
             .by(__.values('name'))
             .by(__.in('FROM_SOURCE').values('overall_score').mean()))
         .by(__.in('BELONGS_TO').in('HAS_REVIEW').out('FROM_SOURCE').group()
             .by(__.values('name'))
             .by(__.project('type', 'url', 'reliability_score')
                 .by(__.values('type'))
                 .by(__.values('url'))
                 .by(__.values('reliability_score'))))
         .by(__.in('BELONGS_TO').in('HAS_REVIEW').count())
        """
        
        results = await gremlin_client.execute_query(query)
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"Hotel '{hotel_name}' not found"
            )
        
        result = results[0]
        total_reviews = result.get('total_reviews', 0)
        source_stats = result.get('source_stats', {})
        source_ratings = result.get('source_ratings', {})
        source_details = result.get('source_details', {})
        
        # Process source distribution
        distribution = []
        for source_name, count in source_stats.items():
            percentage = round((count / max(total_reviews, 1)) * 100, 1)
            avg_rating = source_ratings.get(source_name, 0.0)
            details = source_details.get(source_name, {})
            
            distribution.append({
                "source_name": source_name,
                "review_count": count,
                "percentage": percentage,
                "average_rating": round(avg_rating, 2),
                "source_type": details.get('type', 'unknown'),
                "source_url": details.get('url', ''),
                "reliability_score": details.get('reliability_score', 0.0)
            })
        
        # Sort by review count
        distribution.sort(key=lambda x: x["review_count"], reverse=True)
        
        response = {
            "hotel_name": hotel_name,
            "hotel_id": result.get('hotel_id', ''),
            "total_reviews": total_reviews,
            "source_distribution": distribution,
            "primary_sources": distribution[:3],
            "source_diversity_score": len(distribution),
            "generated_at": datetime.now().isoformat()
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting source distribution for hotel {hotel_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve source distribution: {str(e)}"
        )


@router.get("/average/{hotel_name}/accommodations", response_model=Dict[str, Any])
async def get_hotel_accommodation_metrics(
    hotel_name: str = Path(..., description="Hotel name"),
    gremlin_client: SchemaAwareGremlinClient = Depends(get_gremlin_client)
):
    """
    Get accommodation-specific metrics for a hotel.
    
    Returns metrics for different room types and accommodation categories:
    - Room types and their average ratings
    - Occupancy and pricing insights
    - Amenity ratings per accommodation type
    - Guest preference patterns
    """
    if not gremlin_client or not gremlin_client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Graph database not available"
        )
    
    try:
        query = f"""
        g.V().hasLabel('Hotel').has('name', '{hotel_name}').as('hotel')
         .project('hotel_id', 'accommodation_types', 'room_ratings', 'amenity_ratings', 'guest_preferences')
         .by(__.values('id'))
         .by(__.out('OFFERS').group()
             .by(__.values('type'))
             .by(__.project('count', 'average_price', 'features')
                 .by(__.count())
                 .by(__.values('price').mean())
                 .by(__.values('features').fold())))
         .by(__.out('OFFERS').group()
             .by(__.values('type'))
             .by(__.in('STAYED_IN').in('HAS_REVIEW').values('overall_score').mean()))
         .by(__.out('OFFERS').out('HAS_AMENITY').group()
             .by(__.values('name'))
             .by(__.in('HAS_AMENITY').in('STAYED_IN').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', within('amenities', 'facilities')).values('aspect_score').mean()))
         .by(__.out('OFFERS').group()
             .by(__.values('type'))
             .by(__.in('STAYED_IN').in('HAS_REVIEW').count()))
        """
        
        results = await gremlin_client.execute_query(query)
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"Hotel '{hotel_name}' not found"
            )
        
        result = results[0]
        accommodation_types = result.get('accommodation_types', {})
        room_ratings = result.get('room_ratings', {})
        amenity_ratings = result.get('amenity_ratings', {})
        guest_preferences = result.get('guest_preferences', {})
        
        # Process accommodation metrics
        accommodations = []
        for room_type, details in accommodation_types.items():
            avg_rating = room_ratings.get(room_type, 0.0)
            guest_count = guest_preferences.get(room_type, 0)
            
            accommodations.append({
                "accommodation_type": room_type,
                "count": details.get('count', 0),
                "average_price": round(details.get('average_price', 0.0), 2),
                "features": details.get('features', []),
                "average_rating": round(avg_rating, 2),
                "guest_reviews": guest_count,
                "popularity_score": round((guest_count / max(sum(guest_preferences.values()), 1)) * 100, 1)
            })
        
        # Process amenity ratings
        amenities = [
            {
                "amenity_name": name,
                "average_rating": round(rating, 2)
            }
            for name, rating in amenity_ratings.items()
        ]
        amenities.sort(key=lambda x: x["average_rating"], reverse=True)
        
        response = {
            "hotel_name": hotel_name,
            "hotel_id": result.get('hotel_id', ''),
            "accommodation_breakdown": accommodations,
            "top_amenities": amenities[:10],
            "accommodation_diversity": len(accommodations),
            "total_guest_reviews": sum(guest_preferences.values()),
            "generated_at": datetime.now().isoformat()
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting accommodation metrics for hotel {hotel_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve accommodation metrics: {str(e)}"
        )


@router.get("/average/{hotel_name}/aspects", response_model=List[AspectBreakdown])
async def get_hotel_aspect_breakdown(
    hotel_name: str = Path(..., description="Hotel name"),
    include_trends: bool = Query(True, description="Include trend analysis"),
    time_window_days: int = Query(90, ge=30, le=365, description="Time window for trend analysis"),
    gremlin_client: SchemaAwareGremlinClient = Depends(get_gremlin_client)
):
    """
    Get detailed aspect breakdown for a hotel.
    
    Returns comprehensive analysis of all aspects:
    - Cleanliness, service, location, value, amenities, etc.
    - Scores, review counts, sentiment distribution
    - Trend analysis over time
    - Comparative performance insights
    """
    if not gremlin_client or not gremlin_client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Graph database not available"
        )
    
    try:
        # Base query for aspect breakdown
        base_query = f"""
        g.V().hasLabel('Hotel').has('name', '{hotel_name}')
         .in('BELONGS_TO').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').group()
         .by(__.values('name'))
         .by(__.project('average_score', 'review_count', 'sentiment_breakdown', 'score_distribution')
             .by(__.in('ANALYZES_ASPECT').values('aspect_score').mean())
             .by(__.in('ANALYZES_ASPECT').count())
             .by(__.in('ANALYZES_ASPECT').groupCount().by(__.values('sentiment')))
             .by(__.in('ANALYZES_ASPECT').groupCount().by(__.values('aspect_score'))))
        """
        
        results = await gremlin_client.execute_query(base_query)
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"Hotel '{hotel_name}' not found or has no aspect data"
            )
        
        aspect_data = results[0]
        
        # Process each aspect
        aspect_breakdown = []
        for aspect_name, data in aspect_data.items():
            sentiment_breakdown = data.get('sentiment_breakdown', {})
            total_sentiment_reviews = sum(sentiment_breakdown.values())
            
            # Calculate trend if requested
            trending = "stable"
            if include_trends:
                # TODO: Implement actual trend calculation based on time series
                trending = "stable"
            
            breakdown = AspectBreakdown(
                aspect_name=aspect_name,
                average_score=round(data.get('average_score', 0.0), 2),
                review_count=data.get('review_count', 0),
                positive_percentage=round(
                    (sentiment_breakdown.get('positive', 0) / max(total_sentiment_reviews, 1)) * 100, 1
                ),
                negative_percentage=round(
                    (sentiment_breakdown.get('negative', 0) / max(total_sentiment_reviews, 1)) * 100, 1
                ),
                trending=trending
            )
            aspect_breakdown.append(breakdown)
        
        # Sort by average score descending
        aspect_breakdown.sort(key=lambda x: x.average_score, reverse=True)
        
        return aspect_breakdown
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting aspect breakdown for hotel {hotel_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve aspect breakdown: {str(e)}"
        )


@router.get("/reviews", response_model=ReviewResponse)
async def query_reviews(
    language: Optional[str] = Query(None, description="Filter by language code"),
    source: Optional[str] = Query(None, description="Filter by review source"),
    aspect: Optional[str] = Query(None, description="Filter by aspect name"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    hotel: Optional[str] = Query(None, description="Filter by hotel name"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    min_rating: Optional[float] = Query(None, ge=0, le=10, description="Minimum rating"),
    max_rating: Optional[float] = Query(None, ge=0, le=10, description="Maximum rating"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of reviews"),
    offset: int = Query(0, ge=0, description="Number of reviews to skip"),
    gremlin_client: SchemaAwareGremlinClient = Depends(get_gremlin_client)
):
    """
    Query reviews with optional filters.
    
    Supports filtering by:
    - Language, source, aspect, sentiment
    - Hotel name or ID
    - Date range
    - Rating range
    
    Returns reviews with aggregations and applied filters.
    """
    if not gremlin_client or not gremlin_client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Graph database not available"
        )
    
    try:
        # Build dynamic query based on filters
        filters_list = []
        query_parts = ["g.V().hasLabel('Review')"]
        
        if language:
            query_parts.append(f".where(__.out('WRITTEN_IN').has('code', '{language}'))")
            filters_list.append(f"language={language}")
        
        if source:
            query_parts.append(f".where(__.out('FROM_SOURCE').has('name', '{source}'))")
            filters_list.append(f"source={source}")
        
        if hotel:
            query_parts.append(f".where(__.out('HAS_REVIEW').out('BELONGS_TO').has('name', '{hotel}'))")
            filters_list.append(f"hotel={hotel}")
        
        if sentiment:
            query_parts.append(f".where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').has('overall_sentiment', '{sentiment}'))")
            filters_list.append(f"sentiment={sentiment}")
        
        if aspect:
            query_parts.append(f".where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', '{aspect}'))")
            filters_list.append(f"aspect={aspect}")
        
        if min_rating:
            query_parts.append(f".has('overall_score', gte({min_rating}))")
            filters_list.append(f"min_rating={min_rating}")
        
        if max_rating:
            query_parts.append(f".has('overall_score', lte({max_rating}))")
            filters_list.append(f"max_rating={max_rating}")
        
        if start_date:
            query_parts.append(f".has('date', gte('{start_date}'))")
            filters_list.append(f"start_date={start_date}")
        
        if end_date:
            query_parts.append(f".has('date', lte('{end_date}'))")
            filters_list.append(f"end_date={end_date}")
        
        # Get total count
        count_query = "".join(query_parts) + ".count()"
        count_results = await gremlin_client.execute_query(count_query)
        total_count = count_results[0] if count_results else 0
        
        # Get paginated results
        data_query = "".join(query_parts) + f".range({offset}, {offset + limit}).valueMap().with('~tinkerpop.valueMap.tokens')"
        reviews = await gremlin_client.execute_query(data_query)
        
        # Get aggregations
        agg_query = "".join(query_parts) + """
        .project('avg_rating', 'sentiment_dist', 'source_dist', 'language_dist')
        .by(__.values('overall_score').mean())
        .by(__.in('HAS_REVIEW').in('HAS_ANALYSIS').groupCount().by(__.values('overall_sentiment')))
        .by(__.out('FROM_SOURCE').groupCount().by(__.values('name')))
        .by(__.out('WRITTEN_IN').groupCount().by(__.values('code')))
        """
        agg_results = await gremlin_client.execute_query(agg_query)
        aggregations = agg_results[0] if agg_results else {}
        
        # Build filters object
        date_range = None
        if start_date or end_date:
            date_range = DateRangeFilter(
                start_date=datetime.fromisoformat(start_date) if start_date else None,
                end_date=datetime.fromisoformat(end_date) if end_date else None
            )
        
        filters_applied = ReviewFilters(
            language=language,
            source=source,
            aspect=aspect,
            sentiment=sentiment,
            hotel=hotel,
            date_range=date_range,
            min_rating=min_rating,
            max_rating=max_rating
        )
        
        return ReviewResponse(
            reviews=reviews,
            total_count=total_count,
            filters_applied=filters_applied,
            aggregations=aggregations
        )
        
    except Exception as e:
        logger.error(f"Error querying reviews: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query reviews: {str(e)}"
        )
