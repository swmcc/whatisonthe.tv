"""Watchlist schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class WatchlistItemType(str, Enum):
    """Type of watchlist item."""

    CONTENT = "content"
    PERSON = "person"


class PersonRoleFilter(str, Enum):
    """Filter for person roles to watch for."""

    ANY = "any"
    ACTOR = "actor"
    DIRECTOR = "director"


# --- Content schemas ---


class WatchlistContentCreate(BaseModel):
    """Schema for adding content to watchlist."""

    tvdb_id: int = Field(..., description="TVDB ID of the content (movie or series)")
    notes: Optional[str] = Field(None, description="Optional notes")


class WatchlistContentUpdate(BaseModel):
    """Schema for updating watchlist content entry."""

    notes: Optional[str] = Field(None, description="Optional notes")


# --- Person schemas ---


class WatchlistPersonCreate(BaseModel):
    """Schema for adding a person to watchlist."""

    person_id: int = Field(..., description="TVDB ID of the person")
    person_role_filter: PersonRoleFilter = Field(
        PersonRoleFilter.ANY, description="What role to watch for"
    )
    notes: Optional[str] = Field(None, description="Optional notes")


class WatchlistPersonUpdate(BaseModel):
    """Schema for updating watchlist person entry."""

    person_role_filter: Optional[PersonRoleFilter] = None
    notes: Optional[str] = None


# --- Summary schemas for embedded data ---


class ContentSummary(BaseModel):
    """Summary of content for watchlist response."""

    id: int
    tvdb_id: int
    name: str
    content_type: str
    year: Optional[int] = None
    poster_url: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None

    model_config = {"from_attributes": True}


class PersonSummary(BaseModel):
    """Summary of person for watchlist response."""

    id: int
    tvdb_id: int
    full_name: str
    image_url: Optional[str] = None

    model_config = {"from_attributes": True}


# --- Response schemas ---


class WatchlistItemResponse(BaseModel):
    """Schema for watchlist item response."""

    id: int
    user_id: int
    item_type: WatchlistItemType
    content: Optional[ContentSummary] = None
    person: Optional[PersonSummary] = None
    person_role_filter: Optional[PersonRoleFilter] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WatchlistCheckResponse(BaseModel):
    """Schema for checking if item is in watchlist."""

    in_watchlist: bool
    item: Optional[WatchlistItemResponse] = None
