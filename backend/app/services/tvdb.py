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

    def search(self, query: str, limit: int = 10, offset: int = 0) -> list[dict[str, Any]]:
        """
        Search for TV shows and movies with pagination support.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Starting position for pagination

        Returns:
            List of search results with basic information
        """
        try:
            results = self.client.search(query)

            # Apply offset and limit
            start_idx = offset
            end_idx = offset + limit

            # Process and format results
            formatted_results = []
            for result in results[start_idx:end_idx]:
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

            # Movies don't have overview in extended response, fetch from translation
            if not movie.get('overview') and movie.get('overviewTranslations'):
                try:
                    # Try to get English translation first
                    if 'eng' in movie['overviewTranslations']:
                        translation = self.client.get_movie_translation(movie_id, 'eng')
                        if translation and 'overview' in translation:
                            movie['overview'] = translation['overview']
                except Exception as trans_error:
                    print(f"Error fetching movie translation: {trans_error}")

            return movie
        except Exception as e:
            print(f"Error fetching movie {movie_id}: {e}")
            return None

    def get_person_details(self, person_id: int) -> dict[str, Any] | None:
        """
        Get detailed information about a person.

        Args:
            person_id: TVDB person ID

        Returns:
            Detailed person information or None if not found
        """
        try:
            person = self.client.get_person_extended(person_id)

            # Get English biography if available
            if person.get('biographies'):
                for bio in person['biographies']:
                    if isinstance(bio, dict) and bio.get('language') == 'eng':
                        person['biography'] = bio.get('biography')
                        break

            return person
        except Exception as e:
            print(f"Error fetching person {person_id}: {e}")
            return None


# Singleton instance
tvdb_service = TVDBService()
