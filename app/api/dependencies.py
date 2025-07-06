"""
FastAPI dependency injection utilities
"""

from fastapi import HTTPException
from contextvars import ContextVar
from typing import Optional, Any

# Context variable to store app state
_app_state: ContextVar[Optional[Any]] = ContextVar('app_state', default=None)


def set_app_state(state: Any) -> None:
    """Set the app state in the context."""
    _app_state.set(state)


def get_app_state() -> Any:
    """Get the app state from the context."""
    state = _app_state.get()
    if state is None:
        raise HTTPException(
            status_code=503,
            detail="Application state not available"
        )
    return state
