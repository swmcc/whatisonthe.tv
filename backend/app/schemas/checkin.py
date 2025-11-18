"""Checkin schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CheckinBase(BaseModel):
    """Base checkin schema."""

    content_id: int = Field(..., description="ID of the content (movie or series)")
    episode_id: Optional[int] = Field(None, description="ID of the episode (for TV show check-ins)")
    watched_at: datetime = Field(..., description="Date and time when the content was watched")
    location: Optional[str] = Field(None, max_length=255, description="Where the content was watched")
    watched_with: Optional[str] = Field(None, max_length=255, description="Who the content was watched with")
    notes: Optional[str] = Field(None, description="Additional notes about the viewing")


class CheckinCreate(CheckinBase):
    """Schema for creating a checkin."""

    pass


class CheckinUpdate(BaseModel):
    """Schema for updating a checkin."""

    watched_at: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=255)
    watched_with: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class ContentSummary(BaseModel):
    """Summary of content for checkin response."""

    id: int
    name: str
    content_type: str
    year: Optional[int] = None
    poster_url: Optional[str] = None

    model_config = {"from_attributes": True}


class EpisodeSummary(BaseModel):
    """Summary of episode for checkin response."""

    id: int
    name: Optional[str] = None
    season_number: int
    episode_number: int
    image_url: Optional[str] = None

    model_config = {"from_attributes": True}


class CheckinResponse(CheckinBase):
    """Schema for checkin response."""

    id: int
    user_id: int
    content: ContentSummary
    episode: Optional[EpisodeSummary] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
