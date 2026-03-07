"""Schemas package."""

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserCreate,
    UserPasswordUpdate,
    UserResponse,
    UserUpdate,
)
from app.schemas.checkin import (
    CheckinCreate,
    CheckinResponse,
    CheckinUpdate,
    ContentSummary,
    EpisodeSummary,
)
from app.schemas.watchlist import (
    WatchlistCheckResponse,
    WatchlistContentCreate,
    WatchlistContentUpdate,
    WatchlistItemResponse,
    WatchlistItemType,
    WatchlistPersonCreate,
    WatchlistPersonUpdate,
    PersonRoleFilter,
)
from app.schemas.watchlist_update import (
    UpdateType,
    WatchlistUpdateResponse,
    WatchlistUpdatesCountResponse,
)

__all__ = [
    "LoginRequest",
    "LoginResponse",
    "UserCreate",
    "UserPasswordUpdate",
    "UserResponse",
    "UserUpdate",
    "CheckinCreate",
    "CheckinResponse",
    "CheckinUpdate",
    "ContentSummary",
    "EpisodeSummary",
    "WatchlistCheckResponse",
    "WatchlistContentCreate",
    "WatchlistContentUpdate",
    "WatchlistItemResponse",
    "WatchlistItemType",
    "WatchlistPersonCreate",
    "WatchlistPersonUpdate",
    "PersonRoleFilter",
    "UpdateType",
    "WatchlistUpdateResponse",
    "WatchlistUpdatesCountResponse",
]
