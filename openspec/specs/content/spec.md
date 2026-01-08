# Content Domain Specification

## Overview

The content domain manages TV series and movies from TheTVDB API. Content is cached locally with a DB-first approach, fetching from the API only when data is missing or stale.

## Models

### Content (Base)
- `id`: Primary key (auto-increment)
- `tvdb_id`: TVDB identifier (unique, indexed)
- `content_type`: "series" or "movie"
- `name`: Display title
- `slug`: URL-friendly identifier
- `overview`: Description/synopsis
- `year`: Release year
- `status`: Current status (e.g., "Continuing", "Ended")
- `image_url`: Primary image
- `poster_url`: Poster image
- `backdrop_url`: Backdrop image
- `original_language`: Language code
- `original_country`: Country code
- `popularity_score`: Ranking metric
- `tvdb_last_updated`: Last TVDB update timestamp
- `last_synced_at`: Local sync timestamp
- `extra_metadata`: JSON blob for additional data

### SeriesDetail
- `content_id`: FK to Content
- `number_of_seasons`: Total season count
- `number_of_episodes`: Total episode count
- `average_runtime`: Typical episode length

### MovieDetail
- `content_id`: FK to Content
- `runtime`: Movie duration in minutes

### Season
- `id`: Primary key
- `tvdb_id`: TVDB identifier
- `content_id`: FK to Content
- `season_number`: Season number
- `name`: Season name
- `overview`: Season description
- `image_url`: Season poster
- `episode_count`: Number of episodes

### Episode
- `id`: Primary key
- `tvdb_id`: TVDB identifier
- `content_id`: FK to Content
- `season_id`: FK to Season
- `season_number`: Season number
- `episode_number`: Episode number within season
- `name`: Episode title
- `overview`: Episode description
- `runtime`: Episode duration
- `aired_at`: Air date
- `image_url`: Episode still

### Person
- `id`: Primary key
- `tvdb_id`: TVDB identifier
- `name`: Display name
- `image_url`: Person photo
- `birth_date`: Date of birth
- `death_date`: Date of death (if applicable)
- `bio`: Biography text

### Credit
- `id`: Primary key
- `content_id`: FK to Content
- `person_id`: FK to Person
- `role_type`: "actor", "director", "writer", "producer", "executive_producer"
- `character_name`: Character name (for actors)
- `sort_order`: Display order

## Requirements

### CONTENT-001: Search Content
The system MUST allow searching for TV series and movies.

**Acceptance Criteria:**
- GET `/search` SHALL accept query parameter `q`
- Results MUST include series, movies, and persons from TVDB
- Results SHALL include id, name, type, overview, year, image_url
- Pagination MUST be supported via `limit` and `offset` parameters
- Response MUST indicate if more results exist via `has_more`

### CONTENT-002: Get Series Details
The system MUST provide detailed series information.

**Acceptance Criteria:**
- GET `/series/{series_id}` SHALL accept TVDB series ID
- Response MUST include series metadata, genres, and credits
- If series not in database, system SHALL fetch from TVDB API
- If series is stale (>7 days), system SHALL queue background refresh
- Non-existent series SHALL return 404 Not Found

### CONTENT-003: Get Movie Details
The system MUST provide detailed movie information.

**Acceptance Criteria:**
- GET `/movie/{movie_id}` SHALL accept TVDB movie ID
- Response MUST include movie metadata, genres, and credits
- If movie not in database, system SHALL fetch from TVDB API
- If movie is stale (>7 days), system SHALL queue background refresh
- Non-existent movie SHALL return 404 Not Found

### CONTENT-004: Get Person Details
The system MUST provide person information with filmography.

**Acceptance Criteria:**
- GET `/person/{person_id}` SHALL accept TVDB person ID
- Response MUST include person details and their credits
- Credits SHOULD include both series and movies

### CONTENT-005: Get Series Seasons
The system MUST list all seasons for a series.

**Acceptance Criteria:**
- GET `/series/{series_id}/seasons` SHALL return all seasons
- Seasons SHALL be ordered by season_number
- Each season MUST include season_number, name, episode_count

### CONTENT-006: Get Series Episodes
The system MUST list all episodes for a series.

**Acceptance Criteria:**
- GET `/series/{series_id}/episodes` SHALL return all episodes
- Episodes SHALL be ordered by season_number, then episode_number
- Each episode MUST include season_number, episode_number, name, aired_at

### CONTENT-007: Get Season Episodes
The system MUST list episodes for a specific season.

**Acceptance Criteria:**
- GET `/series/{series_id}/season/{season_number}/episodes` SHALL return season episodes
- Episodes SHALL be ordered by episode_number
- Non-existent season SHALL return empty list

### CONTENT-008: Background Content Sync
The system MUST synchronize full content data in background.

**Acceptance Criteria:**
- After basic content creation, system SHALL queue full sync task
- Full sync MUST include genres, credits, seasons, and episodes
- Sync tasks SHALL use Celery for async processing
- Failed syncs SHALL be logged and retryable

## Scenarios

### Scenario: Search for TV Series
```
GIVEN the TVDB API contains series "Breaking Bad"
WHEN user searches for "breaking bad"
THEN results include the series with correct metadata
AND result type is "series"
```

### Scenario: Search Pagination
```
GIVEN a search for "star" returns 100 results
WHEN user requests with limit=20, offset=0
THEN exactly 20 results are returned
AND has_more is true
```

### Scenario: Fresh Content from Cache
```
GIVEN "The Office" was synced 2 days ago
WHEN user requests series details
THEN data is returned from database
AND no API call is made
```

### Scenario: Stale Content Refresh
```
GIVEN "Friends" was last synced 10 days ago
WHEN user requests series details
THEN cached data is returned immediately
AND background sync is queued for refresh
```

### Scenario: New Content First Access
```
GIVEN "New Show" is not in local database
WHEN user requests series details
THEN system fetches from TVDB API
AND basic record is saved to database
AND full sync is queued in background
```

### Scenario: Aired Order Episodes Only
```
GIVEN a series has episodes in multiple orderings
WHEN system syncs episode data
THEN only "Aired Order" episodes are stored
AND alternate orderings are excluded
```

## Caching Strategy

1. **Cache Duration:** Content is considered fresh for 7 days
2. **Cache Miss:** Fetch from TVDB API, save basic record, queue full sync
3. **Cache Hit (Fresh):** Return from database immediately
4. **Cache Hit (Stale):** Return from database, queue background refresh
5. **Background Sync:** Updates genres, credits, seasons, episodes

## Data Consistency

- TVDB IDs are the canonical external reference
- Internal auto-increment IDs are used for foreign keys
- Content type enum restricts to "series" or "movie"
- Duplicate detection uses tvdb_id unique constraint
