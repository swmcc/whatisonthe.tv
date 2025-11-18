"""Checkin API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.checkin import Checkin
from app.models.content import Content
from app.models.episode import Episode
from app.models.user import User
from app.schemas.checkin import CheckinCreate, CheckinResponse, CheckinUpdate

router = APIRouter(prefix="/checkins", tags=["checkins"])


@router.post("", response_model=CheckinResponse, status_code=status.HTTP_201_CREATED)
async def create_checkin(
    checkin_data: CheckinCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new checkin for the current user.

    Args:
        checkin_data: Checkin creation data (content_id is TVDB ID)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created checkin

    Raises:
        HTTPException: If content or episode cannot be found/created
    """
    # Look up content by TVDB ID
    content_result = await db.execute(
        select(Content).where(Content.tvdb_id == checkin_data.content_id)
    )
    content = content_result.scalar_one_or_none()

    # If content not in DB, trigger background sync for next time
    if not content:
        # Queue sync tasks for future check-ins
        from app.tasks.content import save_movie_full, save_series_full

        # Trigger background save (these run async via Celery)
        try:
            save_movie_full.delay(checkin_data.content_id)
        except:
            pass
        try:
            save_series_full.delay(checkin_data.content_id)
        except:
            pass

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content not found in database. Please view the content detail page first, then try checking in again.",
        )

    # If episode_id provided, verify it exists and belongs to the content
    episode = None
    if checkin_data.episode_id:
        # Look up episode by TVDB ID
        episode_result = await db.execute(
            select(Episode).where(Episode.tvdb_id == checkin_data.episode_id)
        )
        episode = episode_result.scalar_one_or_none()
        if not episode:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Episode with TVDB ID {checkin_data.episode_id} not found. Please ensure the series and its episodes are loaded.",
            )
        if episode.content_id != content.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Episode does not belong to the specified content",
            )

    # Create checkin using internal database IDs
    checkin = Checkin(
        user_id=current_user.id,
        content_id=content.id,  # Use internal DB ID
        episode_id=episode.id if episode else None,  # Use internal DB ID
        watched_at=checkin_data.watched_at,
        location=checkin_data.location,
        watched_with=checkin_data.watched_with,
        notes=checkin_data.notes,
    )

    db.add(checkin)
    await db.commit()
    await db.refresh(checkin)

    # Load relationships for response
    result = await db.execute(
        select(Checkin)
        .where(Checkin.id == checkin.id)
        .options(selectinload(Checkin.content), selectinload(Checkin.episode))
    )
    checkin = result.scalar_one()

    return CheckinResponse.model_validate(checkin)


@router.get("", response_model=list[CheckinResponse])
async def list_checkins(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """
    List all checkins for the current user.

    Args:
        current_user: Current authenticated user
        db: Database session
        limit: Maximum number of checkins to return
        offset: Number of checkins to skip

    Returns:
        List of user's checkins
    """
    result = await db.execute(
        select(Checkin)
        .where(Checkin.user_id == current_user.id)
        .options(selectinload(Checkin.content), selectinload(Checkin.episode))
        .order_by(Checkin.watched_at.desc())
        .limit(limit)
        .offset(offset)
    )
    checkins = result.scalars().all()

    return [CheckinResponse.model_validate(checkin) for checkin in checkins]


@router.get("/{checkin_id}", response_model=CheckinResponse)
async def get_checkin(
    checkin_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific checkin by ID.

    Args:
        checkin_id: ID of the checkin
        current_user: Current authenticated user
        db: Database session

    Returns:
        Checkin details

    Raises:
        HTTPException: If checkin not found or doesn't belong to user
    """
    result = await db.execute(
        select(Checkin)
        .where(Checkin.id == checkin_id)
        .options(selectinload(Checkin.content), selectinload(Checkin.episode))
    )
    checkin = result.scalar_one_or_none()

    if not checkin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkin with id {checkin_id} not found",
        )

    # Ensure checkin belongs to current user
    if checkin.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this checkin",
        )

    return CheckinResponse.model_validate(checkin)


@router.patch("/{checkin_id}", response_model=CheckinResponse)
async def update_checkin(
    checkin_id: int,
    checkin_update: CheckinUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a checkin.

    Args:
        checkin_id: ID of the checkin to update
        checkin_update: Updated checkin data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated checkin

    Raises:
        HTTPException: If checkin not found or doesn't belong to user
    """
    result = await db.execute(select(Checkin).where(Checkin.id == checkin_id))
    checkin = result.scalar_one_or_none()

    if not checkin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkin with id {checkin_id} not found",
        )

    # Ensure checkin belongs to current user
    if checkin.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this checkin",
        )

    # Update fields
    update_data = checkin_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(checkin, field, value)

    await db.commit()
    await db.refresh(checkin)

    # Load relationships for response
    result = await db.execute(
        select(Checkin)
        .where(Checkin.id == checkin.id)
        .options(selectinload(Checkin.content), selectinload(Checkin.episode))
    )
    checkin = result.scalar_one()

    return CheckinResponse.model_validate(checkin)


@router.delete("/{checkin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checkin(
    checkin_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a checkin.

    Args:
        checkin_id: ID of the checkin to delete
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If checkin not found or doesn't belong to user
    """
    result = await db.execute(select(Checkin).where(Checkin.id == checkin_id))
    checkin = result.scalar_one_or_none()

    if not checkin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkin with id {checkin_id} not found",
        )

    # Ensure checkin belongs to current user
    if checkin.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this checkin",
        )

    await db.delete(checkin)
    await db.commit()

    return None


@router.get("/content/{content_id}", response_model=list[CheckinResponse])
async def list_content_checkins(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all checkins for a specific content (movie or series).

    Args:
        content_id: ID of the content
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of checkins for the content
    """
    result = await db.execute(
        select(Checkin)
        .where(Checkin.user_id == current_user.id, Checkin.content_id == content_id)
        .options(selectinload(Checkin.content), selectinload(Checkin.episode))
        .order_by(Checkin.watched_at.desc())
    )
    checkins = result.scalars().all()

    return [CheckinResponse.model_validate(checkin) for checkin in checkins]
