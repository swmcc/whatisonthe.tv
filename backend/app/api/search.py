"""Search API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.tvdb import tvdb_service

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
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
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
        results = tvdb_service.search(q, limit=limit)
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
async def get_series(series_id: int):
    """
    Get detailed information about a TV series.

    Args:
        series_id: TVDB series ID

    Returns:
        Detailed series information
    """
    series = tvdb_service.get_series_details(series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series


@router.get("/movie/{movie_id}")
async def get_movie(movie_id: int):
    """
    Get detailed information about a movie.

    Args:
        movie_id: TVDB movie ID

    Returns:
        Detailed movie information
    """
    movie = tvdb_service.get_movie_details(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.get("/person/{person_id}")
async def get_person(person_id: int):
    """
    Get detailed information about a person (actor, director, writer, etc.).

    Args:
        person_id: TVDB person ID

    Returns:
        Detailed person information including filmography
    """
    person = tvdb_service.get_person_details(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person
