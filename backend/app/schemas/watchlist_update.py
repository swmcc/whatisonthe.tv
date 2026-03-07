"""Watchlist update schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class UpdateType(str, Enum):
    """Type of watchlist update."""

    STATUS_CHANGE = "status_change"
    NEW_EPISODE = "new_episode"
    NEW_CAST = "new_cast"
    METADATA_UPDATE = "metadata_update"


# --- Summary schemas for embedded data ---


class ContentUpdateSummary(BaseModel):
    """Summary of content for update response."""

    id: int
    tvdb_id: int
    name: str
    content_type: str
    year: Optional[int] = None
    poster_url: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None

    model_config = {"from_attributes": True}


class PersonUpdateSummary(BaseModel):
    """Summary of person for update response."""

    id: int
    tvdb_id: int
    full_name: str
    image_url: Optional[str] = None

    model_config = {"from_attributes": True}


class WatchlistItemSummary(BaseModel):
    """Summary of watchlist item for update response."""

    id: int
    item_type: str
    content: Optional[ContentUpdateSummary] = None
    person: Optional[PersonUpdateSummary] = None

    model_config = {"from_attributes": True}


# --- Response schemas ---


class WatchlistUpdateResponse(BaseModel):
    """Schema for watchlist update response."""

    id: int
    user_id: int
    watchlist_item_id: int
    watchlist_item: Optional[WatchlistItemSummary] = None
    update_type: UpdateType
    description: str
    details: Optional[dict] = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WatchlistUpdatesCountResponse(BaseModel):
    """Schema for unread updates count."""

    count: int
