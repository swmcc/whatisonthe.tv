"""Search API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.content_repository import ContentRepository

router = APIRouter()


class SearchResult(BaseModel):
    """Search result model."""

    id: int | None
    name: str | None
    type: str | None
    overview: str | None
    year: str | None
    image_url: str | None
    poster: str | None
    primary_language: str | None
    country: str | None
    status: str | None


class SearchResponse(BaseModel):
    """Search response model."""

    query: str
    results: list[SearchResult]
    count: int
    offset: int
    has_more: bool


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search for TV shows and movies with pagination support.

    Args:
        q: Search query string
        limit: Number of results per page (default: 20, max: 50)
        offset: Starting position for pagination (default: 0)

    Returns:
        Search results with metadata including pagination info
    """
    try:
        repo = ContentRepository(db)
        # Request one extra to check if there are more results
        results = await repo.search(q, limit=limit + 1, offset=offset)

        # Check if there are more results
        has_more = len(results) > limit

        # Return only the requested number of results
        if has_more:
            results = results[:limit]

        return SearchResponse(
            query=q,
            results=results,
            count=len(results),
            offset=offset,
            has_more=has_more
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/series/{series_id}")
async def get_series(series_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get detailed information about a TV series.

    This uses DB-first caching with async background sync:
    1. Check DB for cached data
    2. If found and fresh (<7 days), return from DB
    3. If not found or stale, get from API
    4. Queue background task to save/update DB
    5. Return API data immediately (fast!)

    Args:
        series_id: TVDB series ID

    Returns:
        Detailed series information
    """
    repo = ContentRepository(db)
    series = await repo.get_series(series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series


@router.get("/movie/{movie_id}")
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get detailed information about a movie.

    This uses DB-first caching with async background sync.

    Args:
        movie_id: TVDB movie ID

    Returns:
        Detailed movie information
    """
    repo = ContentRepository(db)
    movie = await repo.get_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.get("/person/{person_id}")
async def get_person(person_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get detailed information about a person (actor, director, writer, etc.).

    This uses DB-first caching with async background sync.

    Args:
        person_id: TVDB person ID

    Returns:
        Detailed person information including filmography
    """
    repo = ContentRepository(db)
    person = await repo.get_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.get("/series/{series_id}/seasons")
async def get_series_seasons(series_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get all seasons for a TV series.

    This uses DB-first caching - returns data from DB if parent series is fresh.

    Args:
        series_id: TVDB series ID

    Returns:
        List of seasons for the series
    """
    repo = ContentRepository(db)
    seasons = await repo.get_series_seasons(series_id)
    return {"seasons": seasons, "count": len(seasons)}


@router.get("/series/{series_id}/episodes")
async def get_series_episodes(series_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get all episodes for a TV series.

    This uses DB-first caching - returns data from DB if parent series is fresh.

    Args:
        series_id: TVDB series ID

    Returns:
        List of all episodes for the series
    """
    repo = ContentRepository(db)
    episodes = await repo.get_series_episodes(series_id)
    return {"episodes": episodes, "count": len(episodes)}


@router.get("/series/{series_id}/season/{season_number}/episodes")
async def get_season_episodes(
    series_id: int,
    season_number: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get episodes for a specific season of a TV series.

    This uses DB-first caching - returns data from DB if parent series is fresh.

    Args:
        series_id: TVDB series ID
        season_number: Season number

    Returns:
        List of episodes for the specified season
    """
    repo = ContentRepository(db)
    episodes = await repo.get_season_episodes(series_id, season_number)
    return {"season_number": season_number, "episodes": episodes, "count": len(episodes)}
