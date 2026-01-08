# Search Domain Specification

## Overview

The search domain provides unified search across TV series, movies, and people using the TVDB API. Results are returned with pagination support and type indicators.

## Requirements

### SEARCH-001: Unified Content Search
The system MUST search across all content types.

**Acceptance Criteria:**
- GET `/search` SHALL accept query parameter `q` (required, min 1 char)
- Search MUST include TV series, movies, and persons
- Each result MUST indicate its type ("series", "movie", "person")
- Empty query SHALL be rejected with validation error

### SEARCH-002: Search Pagination
The system MUST support paginated search results.

**Acceptance Criteria:**
- `limit` parameter controls results per page (default 20, max 50)
- `offset` parameter controls starting position (default 0)
- Response MUST include:
  - `query`: The search term used
  - `results`: Array of results
  - `count`: Number of results in current response
  - `offset`: Current offset
  - `has_more`: Boolean indicating more results exist

### SEARCH-003: Search Result Format
Search results MUST contain consistent metadata.

**Acceptance Criteria:**
- Each result SHALL include:
  - `id`: TVDB identifier
  - `name`: Display title
  - `type`: Content type ("series", "movie", "person")
  - `overview`: Description/synopsis
  - `year`: Release/birth year
  - `image_url`: Primary image
  - `poster`: Poster image (if available)
  - `primary_language`: Original language
  - `country`: Country of origin
  - `status`: Current status

### SEARCH-004: Error Handling
The system MUST handle search errors gracefully.

**Acceptance Criteria:**
- API failures SHALL return 500 Internal Server Error
- Error response SHALL include descriptive message
- Empty results SHALL return empty array, not error

## Scenarios

### Scenario: Basic Search
```
GIVEN TVDB contains "Breaking Bad" series
WHEN user searches for "breaking bad"
THEN results include the series
AND result type is "series"
AND result includes year, overview, image
```

### Scenario: Multi-Type Results
```
GIVEN search term matches series, movie, and person
WHEN user searches for "star"
THEN results include all matching types
AND each result has correct type indicator
```

### Scenario: Paginated Results
```
GIVEN "star" matches 100 items
WHEN user searches with limit=20, offset=0
THEN 20 results are returned
AND has_more is true
WHEN user searches with limit=20, offset=80
THEN 20 results are returned
AND has_more is false
```

### Scenario: No Results
```
GIVEN no content matches "xyznonexistent123"
WHEN user searches for that term
THEN results array is empty
AND count is 0
AND has_more is false
```

### Scenario: Search Error Recovery
```
GIVEN TVDB API is temporarily unavailable
WHEN user performs search
THEN system returns 500 error
AND error message indicates search failed
```

### Scenario: Minimum Query Length
```
WHEN user searches with empty string
THEN system returns validation error
AND search is not performed
```

## Search Behavior

1. **Relevance:** Results are ordered by TVDB relevance score
2. **Type Mix:** All content types returned together, not segregated
3. **Language:** Primary search is for English content
4. **Images:** Falls back to alternate images if primary unavailable

## Frontend Sorting

The frontend provides additional client-side sorting options:
- Relevance (default, API order)
- Year (newest/oldest)
- Name (A-Z, Z-A)

This sorting is applied to already-fetched results and does not affect API pagination.

## Caching Considerations

- Search results are NOT cached locally
- Each search queries TVDB API fresh
- Individual content items are cached after detail view
- Consider Redis caching for popular searches (future enhancement)
