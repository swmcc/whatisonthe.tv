"""Tests for watchlist updates task module."""

from app.tasks.watchlist_updates import parse_character_credit


class TestParseCharacterCredit:
    """Tests for parse_character_credit helper function."""

    def test_extracts_series_name_when_present(self):
        """Series name should be used for content_name when available."""
        char = {
            "seriesId": 12345,
            "seriesName": "Psych",
            "name": "Gus",
        }
        content_name, character_name = parse_character_credit(char)
        assert content_name == "Psych"
        assert character_name == "Gus"

    def test_extracts_movie_name_when_present(self):
        """Movie name should be used for content_name when available."""
        char = {
            "movieId": 67890,
            "movieName": "Holes",
            "name": "Sam",
        }
        content_name, character_name = parse_character_credit(char)
        assert content_name == "Holes"
        assert character_name == "Sam"

    def test_does_not_use_character_name_for_content_name(self):
        """
        Bug fix test: When seriesName and movieName are missing,
        content_name should NOT fall back to the character name.

        This was the bug: "Dulé Hill cast in 'David' as David" - where
        the character name 'David' was incorrectly used as the content title.
        """
        char = {
            "seriesId": 12345,
            # seriesName is missing!
            "name": "David",  # This is the character name
        }
        content_name, character_name = parse_character_credit(char)
        # content_name should be None (to trigger DB/API lookup), NOT "David"
        assert content_name is None
        assert character_name == "David"

    def test_prefers_series_name_over_movie_name(self):
        """Series name takes precedence over movie name."""
        char = {
            "seriesId": 12345,
            "seriesName": "The Series",
            "movieId": 67890,
            "movieName": "The Movie",
            "name": "Character",
        }
        content_name, character_name = parse_character_credit(char)
        assert content_name == "The Series"

    def test_uses_movie_name_when_series_name_missing(self):
        """Falls back to movie name when series name is missing."""
        char = {
            "movieId": 67890,
            "movieName": "The Movie",
            "name": "Character",
        }
        content_name, character_name = parse_character_credit(char)
        assert content_name == "The Movie"

    def test_returns_none_when_both_names_missing(self):
        """Returns None for content_name when both series and movie names are missing.

        The caller is responsible for looking up the name from DB/API.
        """
        char = {
            "seriesId": 12345,
            "name": "Character",
        }
        content_name, character_name = parse_character_credit(char)
        assert content_name is None

    def test_uses_person_name_as_character_fallback(self):
        """Falls back to personName for character when name is missing."""
        char = {
            "seriesId": 12345,
            "seriesName": "The Show",
            "personName": "Actor Name",
        }
        content_name, character_name = parse_character_credit(char)
        assert character_name == "Actor Name"

    def test_empty_character_when_no_names_available(self):
        """Returns empty string for character when no name fields present."""
        char = {
            "seriesId": 12345,
            "seriesName": "The Show",
        }
        content_name, character_name = parse_character_credit(char)
        assert character_name == ""
