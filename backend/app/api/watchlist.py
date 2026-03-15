"""Watchlist API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.content import Content
from app.models.person import Person
from app.models.user import User
from app.models.watchlist import WatchlistItem, WatchlistItemType
from app.models.watchlist_person_snapshot import WatchlistPersonSnapshot
from app.models.watchlist_content_snapshot import WatchlistContentSnapshot
from app.schemas.watchlist import (
    WatchlistCheckResponse,
    WatchlistContentCreate,
    WatchlistContentUpdate,
    WatchlistItemResponse,
    WatchlistPersonCreate,
    WatchlistPersonUpdate,
)

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=list[WatchlistItemResponse])
async def list_watchlist(
    item_type: WatchlistItemType | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all watchlist items for the current user.

    Args:
        item_type: Optional filter by item type (content or person)
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of watchlist items
    """
    query = (
        select(WatchlistItem)
        .where(WatchlistItem.user_id == current_user.id)
        .options(selectinload(WatchlistItem.content), selectinload(WatchlistItem.person))
        .order_by(WatchlistItem.created_at.desc())
    )

    if item_type:
        query = query.where(WatchlistItem.item_type == item_type)

    result = await db.execute(query)
    items = result.scalars().all()

    return [WatchlistItemResponse.model_validate(item) for item in items]


@router.post("/content", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_content_to_watchlist(
    watchlist_data: WatchlistContentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add content (show/movie) to watchlist.

    Args:
        watchlist_data: Content watchlist data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created watchlist item

    Raises:
        HTTPException: If content not found or already in watchlist
    """
    # Find content by TVDB ID
    result = await db.execute(select(Content).where(Content.tvdb_id == watchlist_data.tvdb_id))
    content = result.scalar_one_or_none()

    # If not in DB, fetch from TVDB and create basic record
    if not content:
        from datetime import datetime
        from app.services.tvdb import tvdb_service
        from app.tasks.content import save_movie_full, save_series_full

        # Try movie first, then series
        api_data = tvdb_service.get_movie_details(watchlist_data.tvdb_id)
        is_movie = True
        if not api_data:
            api_data = tvdb_service.get_series_details(watchlist_data.tvdb_id)
            is_movie = False

        if not api_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content with TVDB ID {watchlist_data.tvdb_id} not found on TVDB",
            )

        # Convert year to int if needed
        year = api_data.get("year")
        if year and isinstance(year, str):
            try:
                year = int(year)
            except (ValueError, TypeError):
                year = None

        # Create basic content record
        content = Content(
            tvdb_id=watchlist_data.tvdb_id,
            content_type="movie" if is_movie else "series",
            name=api_data.get("name"),
            overview=api_data.get("overview"),
            year=year,
            status=api_data.get("status", {}).get("name") if isinstance(api_data.get("status"), dict) else api_data.get("status"),
            image_url=api_data.get("image"),
            last_synced_at=datetime.utcnow(),
        )
        db.add(content)
        await db.flush()

        # Queue background task for full sync
        if is_movie:
            save_movie_full.delay(watchlist_data.tvdb_id, api_data)
        else:
            save_series_full.delay(watchlist_data.tvdb_id, api_data)

    # Check if already in watchlist
    existing = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.content_id == content.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Content already in watchlist",
        )

    # Create watchlist item
    item = WatchlistItem(
        user_id=current_user.id,
        item_type=WatchlistItemType.CONTENT,
        content_id=content.id,
        notes=watchlist_data.notes,
    )

    db.add(item)
    await db.flush()

    # Create snapshot of current cast from TVDB (for series only)
    # This captures all known cast members at the time of adding to watchlist
    if content.content_type == "series":
        from app.services.tvdb import tvdb_service

        # Fetch current details to get characters/cast
        series_data = tvdb_service.get_series_details(content.tvdb_id)
        if series_data:
            api_characters = series_data.get("characters", [])
            snapshot_cast: set[tuple[int, str]] = set()

            for char in api_characters:
                person_id = char.get("peopleId") or char.get("personId")
                if not person_id:
                    continue

                # Track actors in the cast
                cast_key = (person_id, "actor")
                if cast_key not in snapshot_cast:
                    snapshot = WatchlistContentSnapshot(
                        watchlist_item_id=item.id,
                        person_tvdb_id=person_id,
                        role_type="actor",
                    )
                    db.add(snapshot)
                    snapshot_cast.add(cast_key)

    await db.commit()
    await db.refresh(item)

    # Load relationships
    result = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.id == item.id)
        .options(selectinload(WatchlistItem.content), selectinload(WatchlistItem.person))
    )
    item = result.scalar_one()

    return WatchlistItemResponse.model_validate(item)


@router.post("/person", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_person_to_watchlist(
    watchlist_data: WatchlistPersonCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add person (actor/director) to watchlist.

    When a person is added to the watchlist, we also capture a snapshot of their
    current credits from TVDB. This snapshot is used to detect new credits in
    future watchlist update checks.

    Args:
        watchlist_data: Person watchlist data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created watchlist item

    Raises:
        HTTPException: If person not found or already in watchlist
    """
    from app.services.tvdb import tvdb_service

    # Find person by TVDB ID
    result = await db.execute(select(Person).where(Person.tvdb_id == watchlist_data.person_id))
    person = result.scalar_one_or_none()

    # Always fetch from TVDB to get current credits for snapshot
    api_data = tvdb_service.get_person_details(watchlist_data.person_id)
    if not api_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with TVDB ID {watchlist_data.person_id} not found on TVDB",
        )

    # If not in DB, create basic record
    if not person:
        from app.tasks.person import save_person_full

        # Create basic person record
        person = Person(
            tvdb_id=watchlist_data.person_id,
            full_name=api_data.get("name", "Unknown"),
            first_name=api_data.get("firstName"),
            last_name=api_data.get("lastName"),
            image_url=api_data.get("image"),
            biography=api_data.get("biography") if isinstance(api_data.get("biography"), str) else None,
        )
        db.add(person)
        await db.flush()

        # Queue background task for full sync
        save_person_full.delay(watchlist_data.person_id, api_data)

    # Check if already in watchlist
    existing = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.person_id == person.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Person already in watchlist",
        )

    # Create watchlist item
    item = WatchlistItem(
        user_id=current_user.id,
        item_type=WatchlistItemType.PERSON,
        person_id=person.id,
        person_role_filter=watchlist_data.person_role_filter,
        notes=watchlist_data.notes,
    )

    db.add(item)
    await db.flush()

    # Create snapshot of current credits from TVDB
    # This captures all known credits at the time of adding to watchlist
    api_characters = api_data.get("characters", [])
    snapshot_credits: set[tuple[int, str]] = set()

    for char in api_characters:
        series_id = char.get("seriesId")
        movie_id = char.get("movieId")
        content_tvdb_id = series_id or movie_id

        if not content_tvdb_id:
            continue

        # Currently only actor roles are tracked in characters
        credit_key = (content_tvdb_id, "actor")
        if credit_key not in snapshot_credits:
            snapshot = WatchlistPersonSnapshot(
                watchlist_item_id=item.id,
                content_tvdb_id=content_tvdb_id,
                role_type="actor",
            )
            db.add(snapshot)
            snapshot_credits.add(credit_key)

    await db.commit()
    await db.refresh(item)

    # Load relationships
    result = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.id == item.id)
        .options(selectinload(WatchlistItem.content), selectinload(WatchlistItem.person))
    )
    item = result.scalar_one()

    return WatchlistItemResponse.model_validate(item)


@router.patch("/content/{tvdb_id}", response_model=WatchlistItemResponse)
async def update_content_watchlist(
    tvdb_id: int,
    update_data: WatchlistContentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update watchlist content entry.

    Args:
        tvdb_id: TVDB ID of the content
        update_data: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated watchlist item

    Raises:
        HTTPException: If content not found in watchlist
    """
    # Find content by TVDB ID
    content_result = await db.execute(select(Content).where(Content.tvdb_id == tvdb_id))
    content = content_result.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with TVDB ID {tvdb_id} not found",
        )

    # Find watchlist item
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.content_id == content.id,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not in watchlist",
        )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)

    # Load relationships
    result = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.id == item.id)
        .options(selectinload(WatchlistItem.content), selectinload(WatchlistItem.person))
    )
    item = result.scalar_one()

    return WatchlistItemResponse.model_validate(item)


@router.patch("/person/{person_id}", response_model=WatchlistItemResponse)
async def update_person_watchlist(
    person_id: int,
    update_data: WatchlistPersonUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update watchlist person entry.

    Args:
        person_id: TVDB ID of the person
        update_data: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated watchlist item

    Raises:
        HTTPException: If person not found in watchlist
    """
    # Find person by TVDB ID
    person_result = await db.execute(select(Person).where(Person.tvdb_id == person_id))
    person = person_result.scalar_one_or_none()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with TVDB ID {person_id} not found",
        )

    # Find watchlist item
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.person_id == person.id,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not in watchlist",
        )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)

    # Load relationships
    result = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.id == item.id)
        .options(selectinload(WatchlistItem.content), selectinload(WatchlistItem.person))
    )
    item = result.scalar_one()

    return WatchlistItemResponse.model_validate(item)


@router.delete("/content/{tvdb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_content_from_watchlist(
    tvdb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove content from watchlist.

    Args:
        tvdb_id: TVDB ID of the content
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If content not found in watchlist
    """
    # Find content by TVDB ID
    content_result = await db.execute(select(Content).where(Content.tvdb_id == tvdb_id))
    content = content_result.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with TVDB ID {tvdb_id} not found",
        )

    # Find watchlist item
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.content_id == content.id,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not in watchlist",
        )

    await db.delete(item)
    await db.commit()

    return None


@router.delete("/person/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_person_from_watchlist(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove person from watchlist.

    Args:
        person_id: TVDB ID of the person
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If person not found in watchlist
    """
    # Find person by TVDB ID
    person_result = await db.execute(select(Person).where(Person.tvdb_id == person_id))
    person = person_result.scalar_one_or_none()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with TVDB ID {person_id} not found",
        )

    # Find watchlist item
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.person_id == person.id,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not in watchlist",
        )

    await db.delete(item)
    await db.commit()

    return None


@router.get("/check/content/{tvdb_id}", response_model=WatchlistCheckResponse)
async def check_content_in_watchlist(
    tvdb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check if content is in watchlist.

    Args:
        tvdb_id: TVDB ID of the content
        current_user: Current authenticated user
        db: Database session

    Returns:
        Whether content is in watchlist and the item if it exists
    """
    # Find content by TVDB ID
    content_result = await db.execute(select(Content).where(Content.tvdb_id == tvdb_id))
    content = content_result.scalar_one_or_none()

    if not content:
        return WatchlistCheckResponse(in_watchlist=False, item=None)

    # Find watchlist item
    result = await db.execute(
        select(WatchlistItem)
        .where(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.content_id == content.id,
        )
        .options(selectinload(WatchlistItem.content), selectinload(WatchlistItem.person))
    )
    item = result.scalar_one_or_none()

    if item:
        return WatchlistCheckResponse(
            in_watchlist=True,
            item=WatchlistItemResponse.model_validate(item),
        )

    return WatchlistCheckResponse(in_watchlist=False, item=None)


@router.get("/check/person/{person_id}", response_model=WatchlistCheckResponse)
async def check_person_in_watchlist(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check if person is in watchlist.

    Args:
        person_id: TVDB ID of the person
        current_user: Current authenticated user
        db: Database session

    Returns:
        Whether person is in watchlist and the item if it exists
    """
    # Find person by TVDB ID
    person_result = await db.execute(select(Person).where(Person.tvdb_id == person_id))
    person = person_result.scalar_one_or_none()

    if not person:
        return WatchlistCheckResponse(in_watchlist=False, item=None)

    # Find watchlist item
    result = await db.execute(
        select(WatchlistItem)
        .where(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.person_id == person.id,
        )
        .options(selectinload(WatchlistItem.content), selectinload(WatchlistItem.person))
    )
    item = result.scalar_one_or_none()

    if item:
        return WatchlistCheckResponse(
            in_watchlist=True,
            item=WatchlistItemResponse.model_validate(item),
        )

    return WatchlistCheckResponse(in_watchlist=False, item=None)
