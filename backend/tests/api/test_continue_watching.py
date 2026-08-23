"""Tests for the continue-watching API endpoint."""

from datetime import date, datetime, timedelta
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.checkin import (
    CONTINUE_WATCHING_LIMIT,
    _build_continue_watching_item,
    _build_continue_watching_items,
    _count_episodes,
    _select_next_episode,
)
from app.main import app

client = TestClient(app)


def make_episode(episode_id, season_number, episode_number, **overrides):
    """Build a lightweight stand-in for an Episode row."""
    defaults = {
        "id": episode_id,
        "tvdb_id": 900000 + episode_id,
        "content_id": 1,
        "season_number": season_number,
        "episode_number": episode_number,
        "name": f"S{season_number:02d}E{episode_number:02d}",
        "aired": date(2026, 1, 12),
        "runtime": 45,
        "image_url": None,
    }
    defaults.update(overrides)

    return SimpleNamespace(**defaults)


def make_content(content_id=1, **overrides):
    """Build a lightweight stand-in for a series Content row."""
    defaults = {
        "id": content_id,
        "tvdb_id": 431000 + content_id,
        "name": f"Series {content_id}",
        "content_type": "series",
        "year": 2022,
        "image_url": None,
    }
    defaults.update(overrides)

    return SimpleNamespace(**defaults)


class TestContinueWatchingEndpoint:
    """Test the continue-watching HTTP endpoint."""

    def test_continue_watching_requires_auth(self):
        """Test that continue-watching requires authentication."""
        response = client.get("/api/checkins/continue-watching")
        # FastAPI returns 403 when no credentials provided with OAuth2
        assert response.status_code in (401, 403)

    def test_continue_watching_not_parsed_as_checkin_id(self):
        """Test that the path is not swallowed by GET /checkins/{checkin_id}."""
        response = client.get("/api/checkins/continue-watching")
        # A 422 would mean FastAPI tried to parse "continue-watching" as an int
        assert response.status_code != 422

    def test_continue_watching_route_registered_before_checkin_id(self):
        """Test that the literal route is registered ahead of the id route."""
        paths = [getattr(route, "path", None) for route in app.routes]
        assert "/api/checkins/continue-watching" in paths
        assert paths.index("/api/checkins/continue-watching") < paths.index(
            "/api/checkins/{checkin_id}"
        )


class TestSelectNextEpisode:
    """Test the pure next-episode selection helper."""

    def test_lowest_unwatched_episode_wins(self):
        """Test that the lowest (season, episode) unwatched episode is chosen."""
        episodes = [
            make_episode(1, 1, 1),
            make_episode(2, 1, 3),
            make_episode(3, 2, 1),
        ]

        next_episode = _select_next_episode(episodes, {1})

        assert next_episode.id == 2

    def test_ordering_beats_input_order(self):
        """Test that S1E3 beats S2E1 even when listed after it."""
        episodes = [
            make_episode(3, 2, 1),
            make_episode(2, 1, 3),
        ]

        next_episode = _select_next_episode(episodes, set())

        assert (next_episode.season_number, next_episode.episode_number) == (1, 3)

    def test_specials_never_selected(self):
        """Test that season 0 episodes are never chosen as the next episode."""
        episodes = [
            make_episode(10, 0, 1),
            make_episode(11, 0, 2),
            make_episode(12, 1, 1),
        ]

        next_episode = _select_next_episode(episodes, set())

        assert next_episode.id == 12

    def test_fully_watched_series_returns_none(self):
        """Test that a fully watched series has no next episode."""
        episodes = [make_episode(1, 1, 1), make_episode(2, 1, 2)]

        assert _select_next_episode(episodes, {1, 2}) is None

    def test_specials_only_series_returns_none(self):
        """Test that a series with only specials has no next episode."""
        episodes = [make_episode(1, 0, 1), make_episode(2, 0, 2)]

        assert _select_next_episode(episodes, set()) is None

    def test_no_episodes_returns_none(self):
        """Test that a series with no episodes has no next episode."""
        assert _select_next_episode([], set()) is None


class TestCountEpisodes:
    """Test the pure watched/total counting helper."""

    def test_counts_exclude_specials(self):
        """Test that specials count towards neither watched nor total."""
        episodes = [
            make_episode(1, 0, 1),
            make_episode(2, 1, 1),
            make_episode(3, 1, 2),
            make_episode(4, 1, 3),
        ]

        watched, total = _count_episodes(episodes, {1, 2})

        assert (watched, total) == (1, 3)

    def test_duplicate_checkins_count_once(self):
        """Test that repeated check-ins for one episode count once."""
        episodes = [make_episode(1, 1, 1), make_episode(2, 1, 2)]
        # Watched ids are distinct internal episode ids, however many
        # check-ins exist for each
        watched_episode_ids = {1}

        assert _count_episodes(episodes, watched_episode_ids) == (1, 2)

    def test_unwatched_series_counts_zero(self):
        """Test that a series with no check-ins reports zero watched."""
        episodes = [make_episode(1, 1, 1), make_episode(2, 1, 2)]

        assert _count_episodes(episodes, set()) == (0, 2)


class TestBuildContinueWatchingItem:
    """Test building a single continue-watching item."""

    def test_builds_item_from_content_and_episodes(self):
        """Test that an item carries content, next episode and counts."""
        content = make_content(1)
        episodes = [
            make_episode(1, 0, 1),
            make_episode(2, 1, 1),
            make_episode(3, 1, 2),
            make_episode(4, 1, 3),
        ]
        last_watched_at = datetime(2026, 8, 20, 21, 14)

        item = _build_continue_watching_item(content, episodes, {2}, last_watched_at)

        assert item is not None
        assert item.content.tvdb_id == content.tvdb_id
        assert item.content.content_type == "series"
        assert item.next_episode.tvdb_id == 900003
        assert (item.next_episode.season_number, item.next_episode.episode_number) == (1, 2)
        assert item.last_watched_at == last_watched_at
        assert item.watched_episodes == 1
        assert item.total_episodes == 3

    def test_fully_watched_series_yields_none(self):
        """Test that a fully watched series produces no item."""
        episodes = [make_episode(1, 1, 1), make_episode(2, 1, 2)]

        item = _build_continue_watching_item(
            make_content(1), episodes, {1, 2}, datetime(2026, 8, 20)
        )

        assert item is None

    def test_specials_only_series_yields_none(self):
        """Test that a specials-only series produces no item."""
        episodes = [make_episode(1, 0, 1)]

        item = _build_continue_watching_item(
            make_content(1), episodes, set(), datetime(2026, 8, 20)
        )

        assert item is None


class TestBuildContinueWatchingItems:
    """Test assembling the ordered, capped continue-watching list."""

    def test_preserves_last_watched_order(self):
        """Test that items keep the most-recently-watched-first order."""
        contents = {cid: make_content(cid) for cid in (1, 2, 3)}
        episodes_by_content = {
            cid: [make_episode(cid * 10, 1, 1), make_episode(cid * 10 + 1, 1, 2)]
            for cid in (1, 2, 3)
        }
        base = datetime(2026, 8, 20, 21, 0)
        last_watched_by_content = [
            (2, base),
            (3, base - timedelta(days=1)),
            (1, base - timedelta(days=2)),
        ]

        items = _build_continue_watching_items(
            last_watched_by_content, contents, episodes_by_content, set()
        )

        assert [item.content.tvdb_id for item in items] == [431002, 431003, 431001]

    def test_omits_fully_watched_series(self):
        """Test that finished series are dropped from the list."""
        contents = {1: make_content(1), 2: make_content(2)}
        episodes_by_content = {
            1: [make_episode(10, 1, 1)],
            2: [make_episode(20, 1, 1)],
        }
        base = datetime(2026, 8, 20)
        last_watched_by_content = [(1, base), (2, base - timedelta(days=1))]

        items = _build_continue_watching_items(
            last_watched_by_content, contents, episodes_by_content, {10}
        )

        assert [item.content.tvdb_id for item in items] == [431002]

    def test_series_without_episodes_omitted(self):
        """Test that series with no stored episodes are dropped."""
        items = _build_continue_watching_items(
            [(1, datetime(2026, 8, 20))], {1: make_content(1)}, {}, set()
        )

        assert items == []

    def test_caps_items_at_limit(self):
        """Test that the list is capped at CONTINUE_WATCHING_LIMIT entries."""
        content_ids = list(range(1, 31))
        contents = {cid: make_content(cid) for cid in content_ids}
        episodes_by_content = {
            cid: [make_episode(cid * 10, 1, 1)] for cid in content_ids
        }
        base = datetime(2026, 8, 20)
        last_watched_by_content = [
            (cid, base - timedelta(days=index))
            for index, cid in enumerate(content_ids)
        ]

        items = _build_continue_watching_items(
            last_watched_by_content, contents, episodes_by_content, set()
        )

        assert CONTINUE_WATCHING_LIMIT == 20
        assert len(items) == CONTINUE_WATCHING_LIMIT
        assert items[0].content.tvdb_id == 431001
        assert items[-1].content.tvdb_id == 431020

    def test_cap_counts_only_returned_items(self):
        """Test that omitted series do not consume a slot in the cap."""
        content_ids = list(range(1, 31))
        contents = {cid: make_content(cid) for cid in content_ids}
        episodes_by_content = {
            cid: [make_episode(cid * 10, 1, 1)] for cid in content_ids
        }
        base = datetime(2026, 8, 20)
        last_watched_by_content = [
            (cid, base - timedelta(days=index))
            for index, cid in enumerate(content_ids)
        ]
        # First five series are fully watched and must be skipped
        watched_episode_ids = {cid * 10 for cid in content_ids[:5]}

        items = _build_continue_watching_items(
            last_watched_by_content, contents, episodes_by_content, watched_episode_ids
        )

        assert len(items) == CONTINUE_WATCHING_LIMIT
        assert items[0].content.tvdb_id == 431006
