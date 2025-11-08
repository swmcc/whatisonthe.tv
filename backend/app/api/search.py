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


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search for TV shows and movies.

    Args:
        q: Search query string
        limit: Maximum number of results (default: 10, max: 50)

    Returns:
        Search results with metadata
    """
    try:
        repo = ContentRepository(db)
        results = await repo.search(q, limit=limit)
        return SearchResponse(
            query=q,
            results=results,
            count=len(results)
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
