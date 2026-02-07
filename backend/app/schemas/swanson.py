"""Swanson AI recommendation schemas."""

from typing import Optional

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """A search result item for context."""

    id: int
    name: str
    type: str
    year: Optional[int] = None
    genres: Optional[list[str]] = None


class RecommendRequest(BaseModel):
    """Request for AI recommendation."""

    prompt: str = Field(..., description="User's prompt/question")
    search_results: list[SearchResult] = Field(
        default_factory=list,
        description="Current search results to consider",
    )


class RecommendResponse(BaseModel):
    """Response with AI recommendation."""

    recommendation: str = Field(..., description="AI-generated recommendation")
    cached: bool = Field(False, description="Whether this was served from cache")
