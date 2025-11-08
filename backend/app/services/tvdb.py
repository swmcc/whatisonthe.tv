"""TVDB API service."""

from typing import Any

import tvdb_v4_official
from app.core.config import settings


class TVDBService:
    """Service for interacting with TVDB API."""

    def __init__(self):
        """Initialize TVDB client."""
        self.client = tvdb_v4_official.TVDB(
            settings.tvdb_api_key,
            pin=settings.tvdb_pin
        )

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Search for TV shows and movies.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of search results with basic information
        """
        try:
            results = self.client.search(query)

            # Process and format results
            formatted_results = []
            for result in results[:limit]:
                formatted_result = {
                    "id": result.get("tvdb_id"),
                    "name": result.get("name"),
                    "type": result.get("type"),  # 'series' or 'movie'
                    "overview": result.get("overview"),
                    "year": result.get("year"),
                    "image_url": result.get("image_url"),
                    "poster": result.get("thumbnail"),
                    "primary_language": result.get("primary_language"),
                    "country": result.get("country"),
                    "status": result.get("status"),
                }
                formatted_results.append(formatted_result)

            return formatted_results
        except Exception as e:
            print(f"TVDB search error: {e}")
            return []

    def get_series_details(self, series_id: int) -> dict[str, Any] | None:
        """
        Get detailed information about a TV series.

        Args:
            series_id: TVDB series ID

        Returns:
            Detailed series information or None if not found
        """
        try:
            series = self.client.get_series_extended(series_id)
            return series
        except Exception as e:
            print(f"Error fetching series {series_id}: {e}")
            return None

    def get_movie_details(self, movie_id: int) -> dict[str, Any] | None:
        """
        Get detailed information about a movie.

        Args:
            movie_id: TVDB movie ID

        Returns:
            Detailed movie information or None if not found
        """
        try:
            movie = self.client.get_movie_extended(movie_id)
            return movie
        except Exception as e:
            print(f"Error fetching movie {movie_id}: {e}")
            return None


# Singleton instance
tvdb_service = TVDBService()
