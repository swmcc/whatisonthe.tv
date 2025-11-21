"""Checkin API endpoints."""

import asyncio
from datetime import datetime
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
from app.models.series_detail import SeriesDetail
from app.models.movie_detail import MovieDetail
from app.schemas.checkin import CheckinCreate, CheckinResponse, CheckinUpdate
from app.services.content_repository import ContentRepository

router = APIRouter(prefix="/checkins", tags=["checkins"])


async def _get_content_with_retry(
    db: AsyncSession, tvdb_id: int, max_retries: int = 3, delay: float = 0.5
) -> Content | None:
    """
    Get content from DB with retry logic (for background save completion).

    Args:
        db: Database session
        tvdb_id: TVDB ID of content
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        Content object or None
    """
    for attempt in range(max_retries):
        result = await db.execute(
            select(Content).where(Content.tvdb_id == tvdb_id)
        )
        content = result.scalar_one_or_none()
        if content:
            return content
        if attempt < max_retries - 1:
            await asyncio.sleep(delay)
    return None


async def _create_basic_movie(db: AsyncSession, tvdb_id: int, api_data: dict) -> Content:
    """Create basic movie content record (minimal data for immediate check-in)."""
    # Convert year to int if it's a string
    year = api_data.get("year")
    if year and isinstance(year, str):
        try:
            year = int(year)
        except (ValueError, TypeError):
            year = None

    content = Content(
        tvdb_id=tvdb_id,
        content_type="movie",
        name=api_data.get("name"),
        overview=api_data.get("overview"),
        year=year,
        status=api_data.get("status", {}).get("name") if isinstance(api_data.get("status"), dict) else api_data.get("status"),
        image_url=api_data.get("image"),
        original_language=api_data.get("originalLanguage"),
        original_country=api_data.get("originalCountry"),
        last_synced_at=datetime.utcnow(),
        extra_metadata=api_data
    )
    db.add(content)
    await db.flush()

    # Add movie details
    movie_detail = MovieDetail(
        content_id=content.id,
        runtime=api_data.get("runtime"),
    )
    db.add(movie_detail)
    await db.flush()

    return content


async def _create_basic_series(db: AsyncSession, tvdb_id: int, api_data: dict) -> Content:
    """Create basic series content record (minimal data for immediate check-in)."""
    # Convert year to int if it's a string
    year = api_data.get("year")
    if year and isinstance(year, str):
        try:
            year = int(year)
        except (ValueError, TypeError):
            year = None

    content = Content(
        tvdb_id=tvdb_id,
        content_type="series",
        name=api_data.get("name"),
        overview=api_data.get("overview"),
        year=year,
        status=api_data.get("status", {}).get("name") if isinstance(api_data.get("status"), dict) else api_data.get("status"),
        image_url=api_data.get("image"),
        original_language=api_data.get("originalLanguage"),
        original_country=api_data.get("originalCountry"),
        last_synced_at=datetime.utcnow(),
        extra_metadata=api_data
    )
    db.add(content)
    await db.flush()

    # Add series details
    series_detail = SeriesDetail(
        content_id=content.id,
        number_of_seasons=api_data.get("numberOfSeasons"),
        number_of_episodes=api_data.get("numberOfEpisodes"),
        average_runtime=api_data.get("averageRuntime"),
    )
    db.add(series_detail)
    await db.flush()

    return content


@router.post("", response_model=CheckinResponse, status_code=status.HTTP_201_CREATED)
async def create_checkin(
    checkin_data: CheckinCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new checkin for the current user.

    This endpoint uses the same DB-first + API fallback pattern as the detail views.
    If content isn't in the database yet, it will be fetched and saved automatically.

    Args:
        checkin_data: Checkin creation data (content_id is TVDB ID)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created checkin

    Raises:
        HTTPException: If content or episode cannot be found/created
    """
    # Quick check if content already exists in DB
    content = await _get_content_with_retry(db, checkin_data.content_id, max_retries=1, delay=0)

    # If not in DB, fetch and save basic content record immediately
    if not content:
        from app.services.tvdb import tvdb_service
        from app.tasks.content import save_movie_full, save_series_full

        # Fetch from TVDB API
        api_data = tvdb_service.get_movie_details(checkin_data.content_id)
        is_movie = True

        if not api_data:
            api_data = tvdb_service.get_series_details(checkin_data.content_id)
            is_movie = False

        if not api_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content with TVDB ID {checkin_data.content_id} not found on TVDB",
            )

        # Create basic content record immediately (just enough for check-in)
        try:
            if is_movie:
                content = await _create_basic_movie(db, checkin_data.content_id, api_data)
            else:
                content = await _create_basic_series(db, checkin_data.content_id, api_data)

            await db.commit()
            await db.refresh(content)

            # Queue background task for full sync (genres, credits, seasons/episodes)
            if is_movie:
                save_movie_full.delay(checkin_data.content_id, api_data)
            else:
                save_series_full.delay(checkin_data.content_id, api_data)

        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save content: {str(e)}",
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
    days: int = 10,
    before_date: str | None = None,
):
    """
    List all checkins for the current user, grouped by day.

    Args:
        current_user: Current authenticated user
        db: Database session
        days: Number of days to fetch (default 10 for initial load, 3 for pagination)
        before_date: ISO date string to fetch checkins before this date (for infinite scroll)

    Returns:
        List of user's checkins for the requested days
    """
    from datetime import datetime, timedelta

    # Build query
    query = (
        select(Checkin)
        .where(Checkin.user_id == current_user.id)
        .options(selectinload(Checkin.content), selectinload(Checkin.episode))
        .order_by(Checkin.watched_at.desc())
    )

    # If before_date provided, filter checkins before that date
    if before_date:
        try:
            before_dt = datetime.fromisoformat(before_date.replace('Z', '+00:00'))
            query = query.where(Checkin.watched_at < before_dt)
        except (ValueError, AttributeError):
            pass  # Ignore invalid date format

    # Fetch checkins
    result = await db.execute(query.limit(1000))  # Generous limit to get enough for N days
    all_checkins = result.scalars().all()

    # Group by day and limit to requested number of days
    from collections import defaultdict
    days_dict = defaultdict(list)

    for checkin in all_checkins:
        day_key = checkin.watched_at.date()
        days_dict[day_key].append(checkin)

    # Get the requested number of days (sorted)
    sorted_days = sorted(days_dict.keys(), reverse=True)[:days]

    # Collect checkins from those days only
    filtered_checkins = []
    for day in sorted_days:
        filtered_checkins.extend(days_dict[day])

    # Sort by watched_at descending
    filtered_checkins.sort(key=lambda c: c.watched_at, reverse=True)

    return [CheckinResponse.model_validate(checkin) for checkin in filtered_checkins]


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


@router.get("/user/{username}", response_model=list[CheckinResponse])
async def list_public_checkins(
    username: str,
    db: AsyncSession = Depends(get_db),
    days: int = 10,
    before_date: str | None = None,
):
    """
    List all public checkins for a user by username (no authentication required).

    Args:
        username: Username of the user
        db: Database session
        days: Number of days to fetch (default 10 for initial load, 3 for pagination)
        before_date: ISO date string to fetch checkins before this date (for infinite scroll)

    Returns:
        List of user's public checkins for the requested days

    Raises:
        HTTPException: If user not found or has no username set
    """
    from datetime import datetime, timedelta

    # Find user by username
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username '{username}' not found",
        )

    # Build query
    query = (
        select(Checkin)
        .where(Checkin.user_id == user.id)
        .options(selectinload(Checkin.content), selectinload(Checkin.episode))
        .order_by(Checkin.watched_at.desc())
    )

    # If before_date provided, filter checkins before that date
    if before_date:
        try:
            before_dt = datetime.fromisoformat(before_date.replace('Z', '+00:00'))
            query = query.where(Checkin.watched_at < before_dt)
        except (ValueError, AttributeError):
            pass  # Ignore invalid date format

    # Fetch checkins
    result = await db.execute(query.limit(1000))  # Generous limit to get enough for N days
    all_checkins = result.scalars().all()

    # Group by day and limit to requested number of days
    from collections import defaultdict
    days_dict = defaultdict(list)

    for checkin in all_checkins:
        day_key = checkin.watched_at.date()
        days_dict[day_key].append(checkin)

    # Get the requested number of days (sorted)
    sorted_days = sorted(days_dict.keys(), reverse=True)[:days]

    # Collect checkins from those days only
    filtered_checkins = []
    for day in sorted_days:
        filtered_checkins.extend(days_dict[day])

    # Sort by watched_at descending
    filtered_checkins.sort(key=lambda c: c.watched_at, reverse=True)

    return [CheckinResponse.model_validate(checkin) for checkin in filtered_checkins]
