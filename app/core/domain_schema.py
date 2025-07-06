"""
Domain schema definition for the Hotel Review Graph RAG system.

This module defines the structure of vertices (nodes) and edges (relationships)
in the graph database, providing a clear specification of the data model
for hotel reviews, sentiment analysis, and related entities.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from enum import Enum
from datetime import datetime


"""
Domain schema definition for the Hotel Review Graph RAG system.

This module defines the structure of vertices (nodes) and edges (relationships)
in the graph database, providing a clear specification of the data model
for hotel reviews, sentiment analysis, and related entities.

Enhanced with property type definitions, validation, and utility functions
for schema-aware operations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from enum import Enum
from datetime import datetime


class PropertyType(str, Enum):
    """Supported property data types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    JSON = "json"
    UUID = "uuid"


@dataclass
class Property:
    """Enhanced property definition with type information and constraints."""
    name: str
    type: PropertyType
    description: str
    required: bool = False
    indexed: bool = False
    unique: bool = False
    default_value: Optional[Any] = None
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Vertex:
    """Enhanced vertex definition with typed properties."""
    label: str
    description: str
    properties: Dict[str, Property] = field(default_factory=dict)
    
    def add_property(self, name: str, prop_type: PropertyType, description: str, 
                    required: bool = False, indexed: bool = False, unique: bool = False,
                    default_value: Optional[Any] = None, **constraints) -> None:
        """Add a typed property to this vertex."""
        self.properties[name] = Property(
            name=name,
            type=prop_type,
            description=description,
            required=required,
            indexed=indexed,
            unique=unique,
            default_value=default_value,
            constraints=constraints
        )


@dataclass
class Edge:
    """Enhanced edge definition with typed properties."""
    label: str
    out_v: str  # Source vertex label
    in_v: str   # Target vertex label
    description: str
    properties: Dict[str, Property] = field(default_factory=dict)
    
    def add_property(self, name: str, prop_type: PropertyType, description: str,
                    required: bool = False, indexed: bool = False,
                    default_value: Optional[Any] = None, **constraints) -> None:
        """Add a typed property to this edge."""
        self.properties[name] = Property(
            name=name,
            type=prop_type,
            description=description,
            required=required,
            indexed=indexed,
            default_value=default_value,
            constraints=constraints
        )


# Vertex Definitions with Enhanced Typing -----------------------------------------------------
def _create_hotel_group_vertex() -> Vertex:
    """Create HotelGroup vertex definition with typed properties."""
    vertex = Vertex(
        label="HotelGroup",
        description="Hotel chain or group that owns multiple properties"
    )
    vertex.add_property("id", PropertyType.UUID, "unique identifier for the hotel group", 
                       required=True, unique=True, indexed=True)
    vertex.add_property("name", PropertyType.STRING, "name of the hotel group/chain", 
                       required=True, indexed=True)
    vertex.add_property("headquarters", PropertyType.STRING, "location of headquarters")
    vertex.add_property("founded", PropertyType.INTEGER, "year founded", 
                       min_value=1800, max_value=2024)
    vertex.add_property("website", PropertyType.STRING, "official website URL")
    vertex.add_property("created_at", PropertyType.DATETIME, "record creation timestamp", 
                       required=True)
    vertex.add_property("updated_at", PropertyType.DATETIME, "last update timestamp")
    return vertex


def _create_hotel_vertex() -> Vertex:
    """Create Hotel vertex definition with typed properties."""
    vertex = Vertex(
        label="Hotel",
        description="Individual hotel property within a group or independent"
    )
    vertex.add_property("id", PropertyType.UUID, "unique hotel identifier", 
                       required=True, unique=True, indexed=True)
    vertex.add_property("name", PropertyType.STRING, "hotel name", required=True, indexed=True)
    vertex.add_property("address", PropertyType.STRING, "full address")
    vertex.add_property("city", PropertyType.STRING, "city location", indexed=True)
    vertex.add_property("country", PropertyType.STRING, "country location", indexed=True)
    vertex.add_property("latitude", PropertyType.FLOAT, "latitude coordinate", 
                       min_value=-90.0, max_value=90.0)
    vertex.add_property("longitude", PropertyType.FLOAT, "longitude coordinate", 
                       min_value=-180.0, max_value=180.0)
    vertex.add_property("star_rating", PropertyType.INTEGER, "official star rating", 
                       min_value=1, max_value=5)
    vertex.add_property("phone", PropertyType.STRING, "contact phone number")
    vertex.add_property("email", PropertyType.STRING, "contact email")
    vertex.add_property("check_in", PropertyType.STRING, "check-in time")
    vertex.add_property("check_out", PropertyType.STRING, "check-out time")
    vertex.add_property("created_at", PropertyType.DATETIME, "record creation timestamp", 
                       required=True)
    vertex.add_property("updated_at", PropertyType.DATETIME, "last update timestamp")
    return vertex


def _create_review_vertex() -> Vertex:
    """Create Review vertex definition with typed properties."""
    vertex = Vertex(
        label="Review",
        description="User-generated review of a hotel stay"
    )
    vertex.add_property("id", PropertyType.UUID, "unique review identifier", 
                       required=True, unique=True, indexed=True)
    vertex.add_property("score", PropertyType.FLOAT, "overall rating (1-10)", 
                       required=True, indexed=True, min_value=1.0, max_value=10.0)
    vertex.add_property("title", PropertyType.STRING, "review title/headline")
    vertex.add_property("text", PropertyType.STRING, "full review text content", required=True)
    vertex.add_property("created_at", PropertyType.DATETIME, "timestamp when review was created", 
                       required=True, indexed=True)
    vertex.add_property("stay_date", PropertyType.DATETIME, "date of hotel stay")
    vertex.add_property("verified", PropertyType.BOOLEAN, "whether stay is verified")
    vertex.add_property("helpful_votes", PropertyType.INTEGER, "number of helpful votes", 
                       min_value=0)
    vertex.add_property("author_name", PropertyType.STRING, "name of reviewer (if available)", 
                       indexed=True)
    return vertex


def _create_analysis_vertex() -> Vertex:
    """Create Analysis vertex definition with typed properties."""
    vertex = Vertex(
        label="Analysis",
        description="AI-generated sentiment or aspect analysis of a review"
    )
    vertex.add_property("id", PropertyType.UUID, "unique analysis identifier", 
                       required=True, unique=True)
    vertex.add_property("sentiment_score", PropertyType.FLOAT, "overall sentiment score (-1 to 1)", 
                       min_value=-1.0, max_value=1.0)
    vertex.add_property("confidence", PropertyType.FLOAT, "confidence level of analysis (0-1)", 
                       min_value=0.0, max_value=1.0)
    vertex.add_property("aspect_score", PropertyType.FLOAT, "specific aspect score (0-5)", 
                       min_value=0.0, max_value=5.0)
    vertex.add_property("explanation", PropertyType.STRING, "brief explanation of the analysis")
    vertex.add_property("model_version", PropertyType.STRING, "version of AI model used")
    vertex.add_property("analyzed_at", PropertyType.DATETIME, "timestamp of analysis", required=True)
    return vertex


# Create enhanced definitions for other vertices
def _create_aspect_vertex() -> Vertex:
    vertex = Vertex(
        label="Aspect",
        description="Specific aspect of hotel service being evaluated"
    )
    vertex.add_property("id", PropertyType.UUID, "unique aspect identifier", 
                       required=True, unique=True)
    vertex.add_property("name", PropertyType.STRING, "aspect name (e.g., cleanliness, service)", 
                       required=True, indexed=True)
    vertex.add_property("category", PropertyType.STRING, "broader category this aspect belongs to", 
                       indexed=True)
    vertex.add_property("description", PropertyType.STRING, "detailed description of the aspect")
    vertex.add_property("weight", PropertyType.FLOAT, "importance weight for overall scoring", 
                       min_value=0.0, max_value=1.0)
    return vertex


def _create_language_vertex() -> Vertex:
    vertex = Vertex(
        label="Language",
        description="Language used in reviews or hotel communication"
    )
    vertex.add_property("code", PropertyType.STRING, "ISO 639-1 language code (e.g., 'en', 'es')", 
                       required=True, unique=True, indexed=True)
    vertex.add_property("name", PropertyType.STRING, "full language name", required=True)
    vertex.add_property("family", PropertyType.STRING, "language family")
    vertex.add_property("script", PropertyType.STRING, "writing system used")
    return vertex


def _create_source_vertex() -> Vertex:
    vertex = Vertex(
        label="Source",
        description="Platform or website where review was published"
    )
    vertex.add_property("id", PropertyType.UUID, "unique source identifier", 
                       required=True, unique=True)
    vertex.add_property("name", PropertyType.STRING, "source platform name", 
                       required=True, indexed=True)
    vertex.add_property("url", PropertyType.STRING, "base URL of the platform")
    vertex.add_property("type", PropertyType.STRING, "type of platform (OTA, review site, etc.)", 
                       indexed=True)
    vertex.add_property("api_version", PropertyType.STRING, "API version if applicable")
    vertex.add_property("reliability_score", PropertyType.FLOAT, "reliability rating of the source", 
                       min_value=0.0, max_value=1.0)
    return vertex


def _create_accommodation_type_vertex() -> Vertex:
    vertex = Vertex(
        label="AccommodationType",
        description="Type of accommodation offered by the hotel"
    )
    vertex.add_property("id", PropertyType.UUID, "unique accommodation type identifier", 
                       required=True, unique=True)
    vertex.add_property("name", PropertyType.STRING, "accommodation type name", 
                       required=True, indexed=True)
    vertex.add_property("category", PropertyType.STRING, "broader category (room, suite, apartment)", 
                       indexed=True)
    vertex.add_property("capacity", PropertyType.INTEGER, "typical guest capacity", min_value=1)
    vertex.add_property("amenities", PropertyType.JSON, "standard amenities included")
    vertex.add_property("size_sqm", PropertyType.FLOAT, "typical size in square meters", 
                       min_value=0.0)
    return vertex


def _create_location_vertex() -> Vertex:
    vertex = Vertex(
        label="Location",
        description="Geographic location or area of interest"
    )
    vertex.add_property("id", PropertyType.UUID, "unique location identifier", 
                       required=True, unique=True)
    vertex.add_property("name", PropertyType.STRING, "location name", required=True, indexed=True)
    vertex.add_property("type", PropertyType.STRING, "location type (city, district, landmark)", 
                       indexed=True)
    vertex.add_property("latitude", PropertyType.FLOAT, "latitude coordinate", 
                       min_value=-90.0, max_value=90.0)
    vertex.add_property("longitude", PropertyType.FLOAT, "longitude coordinate", 
                       min_value=-180.0, max_value=180.0)
    vertex.add_property("timezone", PropertyType.STRING, "local timezone")
    vertex.add_property("population", PropertyType.INTEGER, "population if applicable", 
                       min_value=0)
    return vertex


def _create_amenity_vertex() -> Vertex:
    vertex = Vertex(
        label="Amenity",
        description="Hotel facility or service offered to guests"
    )
    vertex.add_property("id", PropertyType.UUID, "unique amenity identifier", 
                       required=True, unique=True)
    vertex.add_property("name", PropertyType.STRING, "amenity name", required=True, indexed=True)
    vertex.add_property("category", PropertyType.STRING, "amenity category", indexed=True)
    vertex.add_property("description", PropertyType.STRING, "detailed description")
    vertex.add_property("is_free", PropertyType.BOOLEAN, "whether amenity is complimentary")
    vertex.add_property("availability", PropertyType.STRING, "availability schedule")
    return vertex


def _create_reviewer_vertex() -> Vertex:
    vertex = Vertex(
        label="Reviewer",
        description="Person who wrote a hotel review"
    )
    vertex.add_property("id", PropertyType.UUID, "unique reviewer identifier", 
                       required=True, unique=True)
    vertex.add_property("username", PropertyType.STRING, "reviewer username/handle", 
                       indexed=True)
    vertex.add_property("join_date", PropertyType.DATETIME, "date joined the platform")
    vertex.add_property("review_count", PropertyType.INTEGER, "total number of reviews written", 
                       min_value=0)
    vertex.add_property("helpful_votes", PropertyType.INTEGER, "total helpful votes received", 
                       min_value=0)
    vertex.add_property("traveler_type", PropertyType.STRING, "type of traveler (business, leisure, etc.)")
    vertex.add_property("location", PropertyType.STRING, "reviewer's location")
    return vertex


# Updated vertices list using factory functions
VERTICES: List[Vertex] = [
    _create_hotel_group_vertex(),
    _create_hotel_vertex(),
    _create_review_vertex(),
    _create_analysis_vertex(),
    _create_aspect_vertex(),
    _create_language_vertex(),
    _create_source_vertex(),
    _create_accommodation_type_vertex(),
    _create_location_vertex(),
    _create_amenity_vertex(),
    _create_reviewer_vertex(),
]

# Edge Definitions with Enhanced Typing -------------------------------------------------------
def _create_owns_edge() -> Edge:
    """Create OWNS edge definition with typed properties."""
    edge = Edge(
        label="OWNS",
        out_v="HotelGroup",
        in_v="Hotel",
        description="Hotel group owns or operates this hotel"
    )
    edge.add_property("since", PropertyType.INTEGER, "year of ownership start", 
                     min_value=1800, max_value=2024)
    edge.add_property("ownership_type", PropertyType.STRING, 
                     "type of ownership (owned, managed, franchised)")
    return edge


def _create_has_review_edge() -> Edge:
    edge = Edge(
        label="HAS_REVIEW",
        out_v="Hotel",
        in_v="Review",
        description="Hotel has received this review"
    )
    edge.add_property("review_date", PropertyType.DATETIME, "date the review was posted")
    edge.add_property("featured", PropertyType.BOOLEAN, "whether review is featured")
    return edge


def _create_wrote_edge() -> Edge:
    edge = Edge(
        label="WROTE",
        out_v="Reviewer",
        in_v="Review",
        description="Reviewer wrote this review"
    )
    edge.add_property("verified_stay", PropertyType.BOOLEAN, "whether the stay was verified")
    return edge


def _create_has_analysis_edge() -> Edge:
    edge = Edge(
        label="HAS_ANALYSIS",
        out_v="Review",
        in_v="Analysis",
        description="Review has this AI-generated analysis"
    )
    edge.add_property("analysis_type", PropertyType.STRING, 
                     "type of analysis (sentiment, aspect, etc.)")
    return edge


def _create_analyzes_aspect_edge() -> Edge:
    edge = Edge(
        label="ANALYZES_ASPECT",
        out_v="Analysis",
        in_v="Aspect",
        description="Analysis evaluates this specific aspect"
    )
    edge.add_property("score", PropertyType.FLOAT, "aspect-specific score", 
                     min_value=0.0, max_value=5.0)
    edge.add_property("confidence", PropertyType.FLOAT, "confidence in this aspect analysis", 
                     min_value=0.0, max_value=1.0)
    return edge


def _create_offers_edge() -> Edge:
    edge = Edge(
        label="OFFERS",
        out_v="Hotel",
        in_v="AccommodationType",
        description="Hotel offers this type of accommodation"
    )
    edge.add_property("room_count", PropertyType.INTEGER, "number of rooms of this type", 
                     min_value=1)
    edge.add_property("base_price", PropertyType.FLOAT, "base price for this accommodation", 
                     min_value=0.0)
    return edge


def _create_provides_edge() -> Edge:
    edge = Edge(
        label="PROVIDES",
        out_v="Hotel",
        in_v="Amenity",
        description="Hotel provides this amenity to guests"
    )
    edge.add_property("included_in_rate", PropertyType.BOOLEAN, "whether included in room rate")
    edge.add_property("additional_cost", PropertyType.FLOAT, "additional cost if applicable", 
                     min_value=0.0)
    return edge


def _create_located_in_edge() -> Edge:
    edge = Edge(
        label="LOCATED_IN",
        out_v="Hotel",
        in_v="Location",
        description="Hotel is located in this area"
    )
    edge.add_property("distance_km", PropertyType.FLOAT, "distance from location center in km", 
                     min_value=0.0)
    edge.add_property("primary", PropertyType.BOOLEAN, "whether this is the primary location")
    return edge


def _create_sourced_from_edge() -> Edge:
    edge = Edge(
        label="SOURCED_FROM",
        out_v="Review",
        in_v="Source",
        description="Review was collected from this source platform"
    )
    edge.add_property("collected_at", PropertyType.DATETIME, 
                     "timestamp when review was collected")
    edge.add_property("source_url", PropertyType.STRING, "original URL of the review")
    return edge


def _create_written_in_edge() -> Edge:
    edge = Edge(
        label="WRITTEN_IN",
        out_v="Review",
        in_v="Language",
        description="Review is written in this language"
    )
    edge.add_property("detected_confidence", PropertyType.FLOAT, 
                     "confidence of language detection", min_value=0.0, max_value=1.0)
    edge.add_property("original", PropertyType.BOOLEAN, "whether this is the original language")
    return edge


def _create_supports_language_edge() -> Edge:
    edge = Edge(
        label="SUPPORTS_LANGUAGE",
        out_v="Hotel",
        in_v="Language",
        description="Hotel staff can communicate in this language"
    )
    edge.add_property("proficiency_level", PropertyType.STRING, "staff proficiency level")
    edge.add_property("availability", PropertyType.STRING, "when language support is available")
    return edge


def _create_refers_to_edge() -> Edge:
    edge = Edge(
        label="REFERS_TO",
        out_v="Review",
        in_v="AccommodationType",
        description="Review specifically mentions this accommodation type"
    )
    edge.add_property("explicitly_mentioned", PropertyType.BOOLEAN, 
                     "whether explicitly mentioned")
    edge.add_property("satisfaction_score", PropertyType.FLOAT, 
                     "satisfaction with this accommodation", min_value=0.0, max_value=10.0)
    return edge


def _create_mentions_edge() -> Edge:
    edge = Edge(
        label="MENTIONS",
        out_v="Review",
        in_v="Amenity",
        description="Review mentions this specific amenity"
    )
    edge.add_property("sentiment", PropertyType.STRING, "sentiment about the amenity")
    edge.add_property("importance", PropertyType.FLOAT, 
                     "how important the amenity was to the experience", 
                     min_value=0.0, max_value=1.0)
    return edge


def _create_competes_with_edge() -> Edge:
    edge = Edge(
        label="COMPETES_WITH",
        out_v="Hotel",
        in_v="Hotel",
        description="Hotels are competitive with each other"
    )
    edge.add_property("competition_level", PropertyType.STRING, "level of competition")
    edge.add_property("market_segment", PropertyType.STRING, "shared market segment")
    return edge


def _create_similar_to_edge() -> Edge:
    edge = Edge(
        label="SIMILAR_TO",
        out_v="Review",
        in_v="Review",
        description="Reviews are semantically similar"
    )
    edge.add_property("similarity_score", PropertyType.FLOAT, "cosine similarity score", 
                     min_value=0.0, max_value=1.0)
    edge.add_property("shared_aspects", PropertyType.JSON, "aspects mentioned in both reviews")
    return edge


# Updated edges list using factory functions
EDGES: List[Edge] = [
    _create_owns_edge(),
    _create_has_review_edge(),
    _create_wrote_edge(),
    _create_has_analysis_edge(),
    _create_analyzes_aspect_edge(),
    _create_offers_edge(),
    _create_provides_edge(),
    _create_located_in_edge(),
    _create_sourced_from_edge(),
    _create_written_in_edge(),
    _create_supports_language_edge(),
    _create_refers_to_edge(),
    _create_mentions_edge(),
    _create_competes_with_edge(),
    _create_similar_to_edge(),
]

# Enhanced Utility Functions ------------------------------------------------------

def get_vertex_by_label(label: str) -> Optional[Vertex]:
    """Get vertex definition by label."""
    for vertex in VERTICES:
        if vertex.label == label:
            return vertex
    return None


def get_edge_by_label(label: str) -> Optional[Edge]:
    """Get edge definition by label."""
    for edge in EDGES:
        if edge.label == label:
            return edge
    return None


def get_edges_for_vertex(vertex_label: str, direction: str = "both") -> List[Edge]:
    """
    Get all edges connected to a vertex.
    
    Args:
        vertex_label: Label of the vertex
        direction: 'in', 'out', or 'both'
    
    Returns:
        List of connected edges
    """
    edges = []
    for edge in EDGES:
        if direction in ["out", "both"] and edge.out_v == vertex_label:
            edges.append(edge)
        if direction in ["in", "both"] and edge.in_v == vertex_label:
            edges.append(edge)
    return edges


def get_vertex_labels() -> List[str]:
    """Get all vertex labels."""
    return [vertex.label for vertex in VERTICES]


def get_edge_labels() -> List[str]:
    """Get all edge labels."""
    return [edge.label for edge in EDGES]


def get_outgoing_edges(vertex_label: str) -> List[Edge]:
    """Get all outgoing edges from a vertex."""
    return [edge for edge in EDGES if edge.out_v == vertex_label]


def get_incoming_edges(vertex_label: str) -> List[Edge]:
    """Get all incoming edges to a vertex."""
    return [edge for edge in EDGES if edge.in_v == vertex_label]


def validate_property_value(value: Any, property_def: Property) -> List[str]:
    """
    Validate a property value against its definition.
    
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    if value is None:
        if property_def.required:
            errors.append(f"Required property '{property_def.name}' cannot be None")
        return errors
    
    # Type validation
    if not _validate_property_type(value, property_def.type):
        errors.append(f"Property '{property_def.name}' has invalid type, expected {property_def.type.value}")
        return errors
    
    # Constraint validation
    constraints = property_def.constraints
    
    if property_def.type in [PropertyType.INTEGER, PropertyType.FLOAT]:
        if "min_value" in constraints and value < constraints["min_value"]:
            errors.append(f"Property '{property_def.name}' value {value} is below minimum {constraints['min_value']}")
        if "max_value" in constraints and value > constraints["max_value"]:
            errors.append(f"Property '{property_def.name}' value {value} exceeds maximum {constraints['max_value']}")
    
    if property_def.type == PropertyType.STRING:
        if "min_length" in constraints and len(value) < constraints["min_length"]:
            errors.append(f"Property '{property_def.name}' is too short (min: {constraints['min_length']})")
        if "max_length" in constraints and len(value) > constraints["max_length"]:
            errors.append(f"Property '{property_def.name}' is too long (max: {constraints['max_length']})")
        if "pattern" in constraints:
            import re
            if not re.match(constraints["pattern"], value):
                errors.append(f"Property '{property_def.name}' does not match required pattern")
    
    return errors


def _validate_property_type(value: Any, expected_type: PropertyType) -> bool:
    """Basic type validation for properties."""
    if value is None:
        return True
    
    if expected_type == PropertyType.STRING:
        return isinstance(value, str)
    elif expected_type == PropertyType.INTEGER:
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == PropertyType.FLOAT:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == PropertyType.BOOLEAN:
        return isinstance(value, bool)
    elif expected_type == PropertyType.DATETIME:
        return isinstance(value, (str, int, datetime))
    elif expected_type == PropertyType.JSON:
        return True  # Any JSON-serializable value
    elif expected_type == PropertyType.UUID:
        return isinstance(value, str) and len(value) > 0  # Basic UUID check
    
    return False


def validate_vertex_properties(vertex_label: str, properties: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Validate properties against vertex schema.
    
    Returns:
        Dict of property names to lists of validation errors
    """
    vertex = get_vertex_by_label(vertex_label)
    if not vertex:
        return {"_schema": [f"Unknown vertex label: {vertex_label}"]}
    
    errors = {}
    
    # Check required properties
    for prop_name, prop_def in vertex.properties.items():
        if prop_def.required and prop_name not in properties:
            errors.setdefault(prop_name, []).append(f"Required property '{prop_name}' is missing")
    
    # Validate provided properties
    for prop_name, value in properties.items():
        if prop_name in vertex.properties:
            prop_errors = validate_property_value(value, vertex.properties[prop_name])
            if prop_errors:
                errors[prop_name] = prop_errors
        else:
            errors.setdefault(prop_name, []).append(f"Unknown property '{prop_name}' for vertex {vertex_label}")
    
    return errors


def validate_edge_properties(edge_label: str, properties: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Validate properties against edge schema.
    
    Returns:
        Dict of property names to lists of validation errors
    """
    edge = get_edge_by_label(edge_label)
    if not edge:
        return {"_schema": [f"Unknown edge label: {edge_label}"]}
    
    errors = {}
    
    # Check required properties
    for prop_name, prop_def in edge.properties.items():
        if prop_def.required and prop_name not in properties:
            errors.setdefault(prop_name, []).append(f"Required property '{prop_name}' is missing")
    
    # Validate provided properties
    for prop_name, value in properties.items():
        if prop_name in edge.properties:
            prop_errors = validate_property_value(value, edge.properties[prop_name])
            if prop_errors:
                errors[prop_name] = prop_errors
        else:
            errors.setdefault(prop_name, []).append(f"Unknown property '{prop_name}' for edge {edge_label}")
    
    return errors


def validate_schema() -> bool:
    """Validate that all edges reference existing vertices."""
    vertex_labels = set(get_vertex_labels())
    
    for edge in EDGES:
        if edge.out_v not in vertex_labels:
            raise ValueError(f"Edge '{edge.label}' references unknown out vertex: {edge.out_v}")
        if edge.in_v not in vertex_labels:
            raise ValueError(f"Edge '{edge.label}' references unknown in vertex: {edge.in_v}")
    
    return True


def get_schema_summary() -> Dict[str, Any]:
    """Get an enhanced summary of the schema."""
    return {
        "vertices": {
            "count": len(VERTICES),
            "labels": get_vertex_labels(),
            "details": [
                {
                    "label": v.label,
                    "description": v.description,
                    "property_count": len(v.properties),
                    "required_properties": [p.name for p in v.properties.values() if p.required],
                    "indexed_properties": [p.name for p in v.properties.values() if p.indexed],
                    "unique_properties": [p.name for p in v.properties.values() if p.unique]
                }
                for v in VERTICES
            ]
        },
        "edges": {
            "count": len(EDGES),
            "labels": get_edge_labels(),
            "details": [
                {
                    "label": e.label,
                    "relationship": f"{e.out_v} -> {e.in_v}",
                    "description": e.description,
                    "property_count": len(e.properties)
                }
                for e in EDGES
            ]
        },
        "connectivity": {
            vertex.label: {
                "outgoing": len(get_outgoing_edges(vertex.label)),
                "incoming": len(get_incoming_edges(vertex.label)),
                "total": len(get_edges_for_vertex(vertex.label))
            }
            for vertex in VERTICES
        },
        "property_types": {
            prop_type.value: sum(
                1 for v in VERTICES 
                for p in v.properties.values() 
                if p.type == prop_type
            ) + sum(
                1 for e in EDGES 
                for p in e.properties.values() 
                if p.type == prop_type
            )
            for prop_type in PropertyType
        }
    }


def get_vertex_property_info(vertex_label: str) -> Dict[str, Any]:
    """Get detailed property information for a vertex."""
    vertex = get_vertex_by_label(vertex_label)
    if not vertex:
        return {}
    
    return {
        "label": vertex.label,
        "description": vertex.description,
        "properties": {
            prop_name: {
                "type": prop.type.value,
                "description": prop.description,
                "required": prop.required,
                "indexed": prop.indexed,
                "unique": prop.unique,
                "constraints": prop.constraints,
                "default_value": prop.default_value
            }
            for prop_name, prop in vertex.properties.items()
        }
    }


def get_edge_property_info(edge_label: str) -> Dict[str, Any]:
    """Get detailed property information for an edge."""
    edge = get_edge_by_label(edge_label)
    if not edge:
        return {}
    
    return {
        "label": edge.label,
        "out_v": edge.out_v,
        "in_v": edge.in_v,
        "description": edge.description,
        "properties": {
            prop_name: {
                "type": prop.type.value,
                "description": prop.description,
                "required": prop.required,
                "indexed": prop.indexed,
                "constraints": prop.constraints,
                "default_value": prop.default_value
            }
            for prop_name, prop in edge.properties.items()
        }
    }


def generate_sample_data(vertex_label: str) -> Dict[str, Any]:
    """Generate sample data for a vertex type."""
    vertex = get_vertex_by_label(vertex_label)
    if not vertex:
        return {}
    
    import uuid
    from datetime import datetime
    
    sample = {}
    
    for prop_name, prop in vertex.properties.items():
        if prop.default_value is not None:
            sample[prop_name] = prop.default_value
        elif prop.type == PropertyType.STRING:
            sample[prop_name] = f"sample_{prop_name}"
        elif prop.type == PropertyType.UUID:
            sample[prop_name] = str(uuid.uuid4())
        elif prop.type == PropertyType.INTEGER:
            min_val = prop.constraints.get("min_value", 1)
            max_val = prop.constraints.get("max_value", 100)
            sample[prop_name] = min_val if min_val else 1
        elif prop.type == PropertyType.FLOAT:
            min_val = prop.constraints.get("min_value", 0.0)
            max_val = prop.constraints.get("max_value", 100.0)
            sample[prop_name] = min_val if min_val else 1.0
        elif prop.type == PropertyType.BOOLEAN:
            sample[prop_name] = True
        elif prop.type == PropertyType.DATETIME:
            sample[prop_name] = datetime.now().isoformat()
        elif prop.type == PropertyType.JSON:
            sample[prop_name] = {"example": "json_data"}
    
    return sample


def get_relationship_paths(start_vertex: str, end_vertex: str, max_depth: int = 3) -> List[List[str]]:
    """
    Find potential relationship paths between two vertex types.
    
    Returns:
        List of paths, where each path is a list of edge labels
    """
    paths = []
    
    def find_paths(current: str, target: str, path: List[str], visited: Set[str], depth: int):
        if depth > max_depth:
            return
        
        if current == target and path:
            paths.append(path.copy())
            return
        
        if current in visited:
            return
        
        visited.add(current)
        
        for edge in get_outgoing_edges(current):
            if edge.in_v not in visited or edge.in_v == target:
                path.append(edge.label)
                find_paths(edge.in_v, target, path, visited, depth + 1)
                path.pop()
        
        visited.remove(current)
    
    find_paths(start_vertex, end_vertex, [], set(), 0)
    return paths


# Export all important symbols
__all__ = [
    # Core classes
    "Vertex", "Edge", "Property", "PropertyType",
    
    # Schema data
    "VERTICES", "EDGES",
    
    # Lookup functions
    "get_vertex_by_label", "get_edge_by_label",
    "get_vertex_labels", "get_edge_labels",
    "get_edges_for_vertex", "get_outgoing_edges", "get_incoming_edges",
    
    # Validation functions
    "validate_vertex_properties", "validate_edge_properties",
    "validate_property_value", "validate_schema",
    
    # Information functions
    "get_schema_summary", "get_vertex_property_info", "get_edge_property_info",
    "generate_sample_data", "get_relationship_paths"
]


# Schema validation on import
if __name__ == "__main__":
    try:
        validate_schema()
        print("✅ Enhanced schema validation passed")
        summary = get_schema_summary()
        print(f"📊 Schema summary:")
        print(f"   - {summary['vertices']['count']} vertices")
        print(f"   - {summary['edges']['count']} edges")
        print(f"   - {sum(summary['property_types'].values())} total properties")
        
        # Show property type distribution
        print(f"📈 Property type distribution:")
        for prop_type, count in summary['property_types'].items():
            if count > 0:
                print(f"   - {prop_type}: {count}")
                
        # Test sample data generation
        print(f"🧪 Sample data for Hotel vertex:")
        hotel_sample = generate_sample_data("Hotel")
        for key, value in list(hotel_sample.items())[:5]:  # Show first 5 properties
            print(f"   - {key}: {value}")
            
    except Exception as e:
        print(f"❌ Enhanced schema validation failed: {e}")
        import traceback
        traceback.print_exc()
