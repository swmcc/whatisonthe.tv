# Check-ins Domain Specification

## Overview

Check-ins record when a user watches content. Users can check in to movies directly or to specific episodes of TV series. Check-ins support optional metadata like location, companions, and notes.

## Models

### Checkin
- `id`: Primary key (auto-increment)
- `user_id`: FK to User
- `content_id`: FK to Content (internal ID)
- `episode_id`: FK to Episode (optional, for TV series)
- `watched_at`: DateTime of viewing
- `location`: Optional viewing location
- `watched_with`: Optional companions
- `notes`: Optional text notes
- `created_at`: Record creation timestamp
- `updated_at`: Record update timestamp

## Requirements

### CHECKIN-001: Create Check-in
Authenticated users MUST be able to record watching content.

**Acceptance Criteria:**
- POST `/checkins` SHALL accept content_id (TVDB ID), watched_at
- Optional fields: episode_id (TVDB ID), location, watched_with, notes
- If content not in database, system SHALL fetch and save it
- For series, episode_id SHOULD be provided
- Response MUST include created check-in with content details
- Returns 201 Created on success

### CHECKIN-002: Create Check-in with New Content
The system MUST support check-ins for content not yet in the database.

**Acceptance Criteria:**
- If content_id references unknown TVDB content, system SHALL fetch from API
- Basic content record MUST be created before check-in
- Full content sync MUST be queued as background task
- Check-in creation SHALL NOT wait for full sync completion

### CHECKIN-003: List User Check-ins
Authenticated users MUST be able to view their check-in history.

**Acceptance Criteria:**
- GET `/checkins` SHALL return current user's check-ins
- Results SHALL be ordered by watched_at descending
- Results SHALL include content and episode details
- Pagination by days parameter (default 10 days)
- `before_date` parameter enables infinite scroll

### CHECKIN-004: Get Single Check-in
Authenticated users MUST be able to view a specific check-in.

**Acceptance Criteria:**
- GET `/checkins/{checkin_id}` SHALL return check-in details
- Response MUST include content and episode information
- Check-in MUST belong to current user or return 403 Forbidden
- Non-existent check-in SHALL return 404 Not Found

### CHECKIN-005: Update Check-in
Authenticated users MUST be able to modify their check-ins.

**Acceptance Criteria:**
- PATCH `/checkins/{checkin_id}` SHALL accept partial updates
- Updatable fields: watched_at, location, watched_with, notes
- Check-in MUST belong to current user or return 403 Forbidden
- Returns updated check-in with content details

### CHECKIN-006: Delete Check-in
Authenticated users MUST be able to remove their check-ins.

**Acceptance Criteria:**
- DELETE `/checkins/{checkin_id}` SHALL remove the check-in
- Check-in MUST belong to current user or return 403 Forbidden
- Returns 204 No Content on success
- Non-existent check-in SHALL return 404 Not Found

### CHECKIN-007: List Content Check-ins
The system MUST list check-ins for specific content.

**Acceptance Criteria:**
- GET `/checkins/content/{tvdb_id}` SHALL return user's check-ins for that content
- Results SHALL include all check-ins (movie or all episodes)
- Results SHALL be ordered by watched_at descending
- Empty list returned if no check-ins exist

### CHECKIN-008: Public Check-in Feed
The system MUST support viewing other users' check-in history.

**Acceptance Criteria:**
- GET `/checkins/user/{username}` SHALL be publicly accessible
- Results SHALL be ordered by watched_at descending
- Pagination by days parameter supported
- Non-existent username SHALL return 404 Not Found

### CHECKIN-009: Episode Verification
When checking in to an episode, the system MUST verify validity.

**Acceptance Criteria:**
- Episode MUST exist in database
- Episode MUST belong to the specified content
- Invalid episode SHALL return 404 Not Found
- Mismatched episode/content SHALL return 400 Bad Request

## Scenarios

### Scenario: Check in to Movie
```
GIVEN an authenticated user
AND movie "Inception" exists with TVDB ID 12345
WHEN user creates check-in with content_id=12345, watched_at="2024-01-15T20:00:00Z"
THEN check-in is created successfully
AND response includes movie details
```

### Scenario: Check in to TV Episode
```
GIVEN an authenticated user
AND series "The Office" with episode "Pilot" exists
WHEN user creates check-in with content_id, episode_id, watched_at
THEN check-in is created for the specific episode
AND response includes series and episode details
```

### Scenario: Check in to New Content
```
GIVEN "New Movie" is not in local database
WHEN user creates check-in with its TVDB ID
THEN system fetches movie from TVDB API
AND basic movie record is saved
AND full sync is queued in background
AND check-in is created successfully
```

### Scenario: View Check-in History
```
GIVEN user has 50 check-ins over 30 days
WHEN user requests check-ins with days=10
THEN only check-ins from last 10 distinct days are returned
AND results are grouped chronologically
```

### Scenario: Infinite Scroll
```
GIVEN user requests check-ins with days=10
AND there are older check-ins beyond day 10
WHEN user requests with before_date=<oldest_date>
THEN next batch of check-ins is returned
```

### Scenario: Prevent Unauthorized Access
```
GIVEN user A has a check-in with id=42
WHEN user B requests GET /checkins/42
THEN system returns 403 Forbidden
```

### Scenario: Public Profile Feed
```
GIVEN user "johndoe" has public check-ins
WHEN anonymous visitor requests /checkins/user/johndoe
THEN check-ins are returned without authentication
```

### Scenario: Episode-Content Mismatch
```
GIVEN episode 111 belongs to series 100
WHEN check-in is created with content_id=200, episode_id=111
THEN system returns 400 Bad Request
AND message indicates episode does not belong to content
```

## Business Rules

1. **Ownership:** Users can only view/modify their own check-ins
2. **Content Creation:** Unknown content is auto-created on first check-in
3. **Episode Association:** Episode check-ins require valid episode-content relationship
4. **Date Grouping:** Check-in lists are grouped by calendar day for UI display
5. **Public Access:** Check-ins are publicly viewable via username endpoint

## Performance Considerations

- Check-ins are eager-loaded with content and episode relationships
- Day-based pagination prevents loading entire history
- Content creation is optimized with basic record + background sync
