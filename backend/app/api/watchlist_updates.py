"""Watchlist updates API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models import User, WatchlistUpdate, WatchlistItem
from app.schemas.watchlist_update import WatchlistUpdateResponse, WatchlistUpdatesCountResponse


router = APIRouter(prefix="/watchlist/updates", tags=["watchlist-updates"])


@router.get("", response_model=list[WatchlistUpdateResponse])
async def get_updates(
    unread_only: bool = False,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get watchlist updates for the current user.

    Args:
        unread_only: If True, only return unread updates
        limit: Maximum number of updates to return
        db: Database session
        current_user: Authenticated user

    Returns:
        List of watchlist updates
    """
    stmt = (
        select(WatchlistUpdate)
        .where(WatchlistUpdate.user_id == current_user.id)
        .options(
            selectinload(WatchlistUpdate.watchlist_item).selectinload(WatchlistItem.content),
            selectinload(WatchlistUpdate.watchlist_item).selectinload(WatchlistItem.person),
        )
        .order_by(WatchlistUpdate.created_at.desc())
        .limit(limit)
    )

    if unread_only:
        stmt = stmt.where(WatchlistUpdate.is_read == False)  # noqa: E712

    result = await db.execute(stmt)
    updates = list(result.scalars().all())

    return updates


@router.get("/count", response_model=WatchlistUpdatesCountResponse)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WatchlistUpdatesCountResponse:
    """
    Get count of unread watchlist updates.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        Count of unread updates
    """
    stmt = select(func.count(WatchlistUpdate.id)).where(
        WatchlistUpdate.user_id == current_user.id,
        WatchlistUpdate.is_read == False,  # noqa: E712
    )

    result = await db.execute(stmt)
    count = result.scalar() or 0

    return WatchlistUpdatesCountResponse(count=count)


@router.post("/{update_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_as_read(
    update_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Mark a single update as read.

    Args:
        update_id: ID of the update to mark as read
        db: Database session
        current_user: Authenticated user
    """
    stmt = select(WatchlistUpdate).where(
        WatchlistUpdate.id == update_id,
        WatchlistUpdate.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    update = result.scalar_one_or_none()

    if not update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Update not found",
        )

    update.is_read = True
    await db.commit()


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Mark all updates as read for the current user.

    Args:
        db: Database session
        current_user: Authenticated user
    """
    from sqlalchemy import update

    stmt = (
        update(WatchlistUpdate)
        .where(
            WatchlistUpdate.user_id == current_user.id,
            WatchlistUpdate.is_read == False,  # noqa: E712
        )
        .values(is_read=True)
    )

    await db.execute(stmt)
    await db.commit()
