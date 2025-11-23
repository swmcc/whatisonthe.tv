#!/usr/bin/env python3
"""
Netflix Viewing History Importer

Imports Netflix viewing history CSV into the check-ins system.
Handles both movies and TV series with intelligent content detection.
"""

import asyncio
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

# API Configuration - default can be overridden via command line
DEFAULT_API_URL = "http://localhost:8000"


class NetflixEntry:
    """Parsed Netflix viewing history entry."""

    def __init__(self, title: str, date_str: str):
        self.raw_title = title
        self.date_str = date_str
        self.content_type = None  # 'movie' or 'series'
        self.show_name = None
        self.season_number = None
        self.episode_name = None
        self.movie_title = None
        self.watched_at = None

        self._parse_title()
        self._parse_date()

    def _parse_title(self):
        """Parse title to determine content type and extract metadata."""
        title = self.raw_title

        # Check for series indicators
        if "Season " in title or "Limited Series:" in title:
            self.content_type = "series"
            self._parse_series_title(title)
        else:
            self.content_type = "movie"
            self.movie_title = title

    def _parse_series_title(self, title: str):
        """
        Parse series title to extract show name, season, and episode.

        Formats:
        - "Show Name: Season 1: Episode Name"
        - "Show Name: Limited Series: Episode Name"
        """
        # Remove "Limited Series:" if present
        title = re.sub(r':\s*Limited Series:', ':', title)

        # Split by colons
        parts = [p.strip() for p in title.split(':')]

        if len(parts) >= 3:
            self.show_name = parts[0]

            # Check if second part contains season number
            season_match = re.search(r'Season (\d+)', parts[1])
            if season_match:
                self.season_number = int(season_match.group(1))
                self.episode_name = parts[2]
            else:
                # No season number, treat as episode name
                self.episode_name = ' '.join(parts[1:])
        elif len(parts) == 2:
            self.show_name = parts[0]
            self.episode_name = parts[1]
        else:
            # Fallback: use whole title as show name
            self.show_name = title

    def _parse_date(self):
        """
        Convert American date (MM/DD/YY) to ISO datetime.
        Assumes UK timezone (GMT/BST).
        """
        try:
            # Parse MM/DD/YY format
            dt = datetime.strptime(self.date_str, "%m/%d/%y")

            # Set time to midnight and add timezone (UTC for simplicity)
            self.watched_at = dt.replace(hour=0, minute=0, second=0, tzinfo=timezone.utc)
        except ValueError as e:
            console.print(f"[red]Failed to parse date '{self.date_str}': {e}[/red]")
            self.watched_at = None

    def __repr__(self):
        if self.content_type == "movie":
            return f"Movie: {self.movie_title} ({self.date_str})"
        else:
            season_info = f"S{self.season_number}" if self.season_number else "Special"
            return f"Series: {self.show_name} - {season_info} - {self.episode_name} ({self.date_str})"


class NetflixImporter:
    """Handles importing Netflix history into check-ins."""

    def __init__(self, api_base_url: str, auth_token: str):
        self.api_base_url = api_base_url
        self.auth_token = auth_token
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=60.0)

        # Stats
        self.total_processed = 0
        self.successful_imports = 0
        self.failed_imports = 0
        self.skipped_imports = 0

    async def search_content(self, query: str, content_type: Optional[str] = None) -> Optional[dict]:
        """
        Search for content by name.

        Args:
            query: Search query (show/movie name)
            content_type: Optional filter ('movie' or 'series')

        Returns:
            First matching result or None
        """
        try:
            response = await self.client.get(
                f"{self.api_base_url}/search",
                params={"q": query, "limit": 10}
            )
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])

            # Filter by type if specified
            if content_type:
                results = [r for r in results if r.get("type") == content_type]

            return results[0] if results else None

        except Exception as e:
            console.print(f"[yellow]Search failed for '{query}': {e}[/yellow]")
            return None

    async def get_series_episodes(self, series_id: int, max_wait: int = 45) -> list[dict]:
        """
        Get episodes for a series, with polling to wait for background fetch.

        Args:
            series_id: TVDB series ID
            max_wait: Maximum seconds to wait for episodes

        Returns:
            List of episode dicts
        """
        # First, trigger series fetch by getting series details
        try:
            response = await self.client.get(f"{self.api_base_url}/series/{series_id}")
            response.raise_for_status()
        except Exception as e:
            console.print(f"[yellow]Failed to fetch series {series_id}: {e}[/yellow]")
            return []

        # Poll for episodes with exponential backoff
        wait_intervals = [2, 3, 5, 5, 10, 10, 10]  # Total: ~45 seconds max

        for interval in wait_intervals:
            await asyncio.sleep(interval)

            try:
                response = await self.client.get(
                    f"{self.api_base_url}/series/{series_id}/episodes"
                )
                response.raise_for_status()
                data = response.json()
                episodes = data.get("episodes", [])

                if episodes:
                    return episodes

            except Exception as e:
                console.print(f"[yellow]Episode fetch attempt failed: {e}[/yellow]")
                continue

        console.print(f"[yellow]No episodes found after {max_wait}s wait for series {series_id}[/yellow]")
        return []

    def find_episode_match(
        self,
        episodes: list[dict],
        season_number: Optional[int],
        episode_name: str
    ) -> Optional[dict]:
        """
        Find episode matching season and name.

        Args:
            episodes: List of episode dicts
            season_number: Season number (None for specials)
            episode_name: Episode name to match

        Returns:
            Matching episode dict or None
        """
        # Filter by season if provided
        if season_number is not None:
            episodes = [e for e in episodes if e.get("season_number") == season_number]

        # Try exact name match first
        for ep in episodes:
            if ep.get("name") and ep["name"].lower() == episode_name.lower():
                return ep

        # Try fuzzy match (contains)
        episode_name_lower = episode_name.lower()
        for ep in episodes:
            if ep.get("name") and episode_name_lower in ep["name"].lower():
                return ep

        # If we have season but no name match, return first episode of season
        if season_number is not None and episodes:
            console.print(f"[yellow]No exact match for '{episode_name}', using first episode of season {season_number}[/yellow]")
            return episodes[0]

        return None

    async def create_checkin(
        self,
        content_id: int,
        episode_id: Optional[int],
        watched_at: datetime
    ) -> bool:
        """
        Create a check-in via API.

        Args:
            content_id: TVDB content ID
            episode_id: TVDB episode ID (None for movies)
            watched_at: When content was watched

        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "content_id": content_id,
                "watched_at": watched_at.isoformat()
            }

            if episode_id is not None:
                payload["episode_id"] = episode_id

            response = await self.client.post(
                f"{self.api_base_url}/checkins",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            console.print(f"[red]Check-in failed (HTTP {e.response.status_code}): {e.response.text}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Check-in failed: {e}[/red]")
            return False

    async def import_movie(self, entry: NetflixEntry) -> bool:
        """Import a movie entry."""
        console.print(f"\n[cyan]Movie:[/cyan] {entry.movie_title}")

        # Search for movie
        result = await self.search_content(entry.movie_title, content_type="movie")
        if not result:
            console.print(f"[red]❌ Movie not found: {entry.movie_title}[/red]")
            return False

        content_id = result.get("id")
        console.print(f"[green]✓ Found:[/green] {result.get('name')} ({result.get('year')}) [TVDB: {content_id}]")

        # Create check-in
        success = await self.create_checkin(content_id, None, entry.watched_at)
        if success:
            console.print(f"[green]✓ Check-in created for {entry.watched_at.strftime('%Y-%m-%d')}[/green]")

        return success

    async def import_series(self, entry: NetflixEntry) -> bool:
        """Import a TV series entry."""
        season_info = f"S{entry.season_number}" if entry.season_number else "Special"
        console.print(f"\n[cyan]Series:[/cyan] {entry.show_name} - {season_info} - {entry.episode_name}")

        # Search for series
        result = await self.search_content(entry.show_name, content_type="series")
        if not result:
            console.print(f"[red]❌ Series not found: {entry.show_name}[/red]")
            return False

        series_id = result.get("id")
        console.print(f"[green]✓ Found series:[/green] {result.get('name')} ({result.get('year')}) [TVDB: {series_id}]")

        # Get episodes (with wait for background fetch)
        console.print("[yellow]⏳ Fetching episodes (may take up to 45s)...[/yellow]")
        episodes = await self.get_series_episodes(series_id)

        if not episodes:
            console.print(f"[red]❌ No episodes found for series {series_id}[/red]")
            return False

        console.print(f"[green]✓ Found {len(episodes)} episodes[/green]")

        # Find matching episode
        episode = self.find_episode_match(episodes, entry.season_number, entry.episode_name)
        if not episode:
            console.print(f"[red]❌ Episode not found: {entry.episode_name}[/red]")
            return False

        episode_id = episode.get("tvdb_id")
        ep_info = f"S{episode.get('season_number')}E{episode.get('episode_number')}: {episode.get('name')}"
        console.print(f"[green]✓ Found episode:[/green] {ep_info} [TVDB: {episode_id}]")

        # Create check-in
        success = await self.create_checkin(series_id, episode_id, entry.watched_at)
        if success:
            console.print(f"[green]✓ Check-in created for {entry.watched_at.strftime('%Y-%m-%d')}[/green]")

        return success

    async def import_entry(self, entry: NetflixEntry) -> bool:
        """Import a single Netflix entry."""
        if entry.watched_at is None:
            console.print(f"[red]❌ Skipping entry with invalid date: {entry.raw_title}[/red]")
            return False

        if entry.content_type == "movie":
            return await self.import_movie(entry)
        else:
            return await self.import_series(entry)

    async def import_from_csv(
        self,
        csv_path: Path,
        limit: Optional[int] = None,
        month: Optional[int] = None,
        year: Optional[int] = None
    ):
        """
        Import entries from Netflix CSV file.

        Args:
            csv_path: Path to CSV file
            limit: Optional limit on number of entries to process
            month: Optional month filter (1-12)
            year: Optional year filter (e.g., 2025)
        """
        console.print(f"\n[bold cyan]Netflix Viewing History Importer[/bold cyan]")
        console.print(f"Reading from: {csv_path}")

        if month or year:
            filter_msg = []
            if month:
                filter_msg.append(f"Month: {month}")
            if year:
                filter_msg.append(f"Year: {year}")
            console.print(f"[yellow]Filtering by: {', '.join(filter_msg)}[/yellow]")
        console.print()

        entries = []

        # Read CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                title = row.get('Title', '').strip('"')
                date = row.get('Date', '').strip('"')

                if title and date:
                    entry = NetflixEntry(title, date)

                    # Apply date filters
                    if entry.watched_at:
                        if month and entry.watched_at.month != month:
                            continue
                        if year and entry.watched_at.year != year:
                            continue

                    entries.append(entry)

                    # Apply limit after filtering
                    if limit and len(entries) >= limit:
                        break

        console.print(f"[bold]Loaded {len(entries)} entries from CSV[/bold]\n")

        # Process entries
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Importing...", total=len(entries))

            for entry in entries:
                self.total_processed += 1

                try:
                    success = await self.import_entry(entry)
                    if success:
                        self.successful_imports += 1
                    else:
                        self.failed_imports += 1
                except Exception as e:
                    console.print(f"[red]❌ Unexpected error: {e}[/red]")
                    self.failed_imports += 1

                progress.update(task, advance=1)

        # Print summary
        console.print(f"\n[bold cyan]Import Summary:[/bold cyan]")
        console.print(f"  Total processed: {self.total_processed}")
        console.print(f"  [green]✓ Successful: {self.successful_imports}[/green]")
        console.print(f"  [red]✗ Failed: {self.failed_imports}[/red]")
        console.print(f"  [yellow]⊘ Skipped: {self.skipped_imports}[/yellow]")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        console.print("[red]Usage: python import_netflix.py <csv_path> <auth_token> [options][/red]")
        console.print("\nOptions:")
        console.print("  --limit N         Limit to N entries")
        console.print("  --month M         Filter by month (1-12)")
        console.print("  --year Y          Filter by year (e.g., 2025)")
        console.print("  --api-url URL     API base URL (default: http://localhost:8000)")
        console.print("\nExamples:")
        console.print("  python import_netflix.py ~/Downloads/NetflixViewingHistory.csv YOUR_TOKEN --limit 25")
        console.print("  python import_netflix.py ~/Downloads/NetflixViewingHistory.csv YOUR_TOKEN --month 11 --year 2025")
        console.print("  python import_netflix.py ~/Downloads/NetflixViewingHistory.csv YOUR_TOKEN --api-url https://example.com")
        sys.exit(1)

    csv_path = Path(sys.argv[1]).expanduser()
    auth_token = sys.argv[2]

    # Parse optional arguments
    limit = None
    month = None
    year = None
    api_url = DEFAULT_API_URL

    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--limit' and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
            i += 2
        elif arg == '--month' and i + 1 < len(sys.argv):
            month = int(sys.argv[i + 1])
            i += 2
        elif arg == '--year' and i + 1 < len(sys.argv):
            year = int(sys.argv[i + 1])
            i += 2
        elif arg == '--api-url' and i + 1 < len(sys.argv):
            api_url = sys.argv[i + 1]
            i += 2
        elif arg.isdigit():
            # Backwards compatibility: treat bare number as limit
            limit = int(arg)
            i += 1
        else:
            i += 1

    if not csv_path.exists():
        console.print(f"[red]Error: File not found: {csv_path}[/red]")
        sys.exit(1)

    console.print(f"[cyan]API URL:[/cyan] {api_url}\n")
    importer = NetflixImporter(api_url, auth_token)

    try:
        await importer.import_from_csv(csv_path, limit, month, year)
    finally:
        await importer.close()


if __name__ == "__main__":
    asyncio.run(main())
