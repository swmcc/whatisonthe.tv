# Authentication Domain Specification

## Overview

The authentication system provides user registration, login, profile management, and public profile access. JWT tokens are used for session management.

## Models

### User
- `id`: Primary key (auto-increment)
- `email`: Unique, required
- `username`: Unique, optional (for public profiles)
- `first_name`: Required
- `last_name`: Required
- `hashed_password`: bcrypt hash
- `created_at`: Timestamp
- `updated_at`: Timestamp

## Requirements

### AUTH-001: User Login
The system MUST authenticate users via email and password.

**Acceptance Criteria:**
- POST `/auth/login` SHALL accept email and password
- On valid credentials, the system SHALL return a JWT access token
- On invalid credentials, the system SHALL return 401 Unauthorized
- The JWT token MUST include the user ID in the `sub` claim

### AUTH-002: Token-Based Authentication
The system MUST validate JWT tokens for protected endpoints.

**Acceptance Criteria:**
- Protected endpoints SHALL require `Authorization: Bearer <token>` header
- Invalid or expired tokens SHALL result in 401 Unauthorized
- The system SHALL extract user identity from the token

### AUTH-003: Get Current User
Authenticated users MUST be able to retrieve their profile.

**Acceptance Criteria:**
- GET `/auth/me` SHALL return current user's profile
- Response MUST include id, email, username, first_name, last_name

### AUTH-004: Update Profile
Authenticated users MUST be able to update their profile.

**Acceptance Criteria:**
- PATCH `/auth/me` SHALL accept username, first_name, last_name
- Only provided fields SHALL be updated
- Username MUST be unique across all users

### AUTH-005: Update Password
Authenticated users MUST be able to change their password.

**Acceptance Criteria:**
- POST `/auth/me/password` SHALL require current_password and new_password
- The system SHALL verify current_password before updating
- Invalid current_password SHALL return 400 Bad Request
- New password MUST be hashed before storage

### AUTH-006: Public User Profiles
The system MUST support public user profile viewing.

**Acceptance Criteria:**
- GET `/auth/user/{username}` SHALL be accessible without authentication
- Response MUST include user's display name
- Response SHOULD NOT expose sensitive information (email)
- Non-existent username SHALL return 404 Not Found

### AUTH-007: Logout
The system SHALL provide a logout endpoint.

**Acceptance Criteria:**
- POST `/auth/logout` SHALL be a protected endpoint
- Client is responsible for discarding the token
- Server MAY return success message

## Scenarios

### Scenario: Successful Login
```
GIVEN a registered user with email "user@example.com" and password "secret123"
WHEN the user submits login credentials
THEN the system returns a JWT access token
AND the token contains the user's ID
```

### Scenario: Invalid Login
```
GIVEN no user with email "unknown@example.com"
WHEN login is attempted with that email
THEN the system returns 401 Unauthorized
AND the message is "Incorrect email or password"
```

### Scenario: Access Protected Resource
```
GIVEN an authenticated user with a valid JWT token
WHEN they request GET /auth/me
THEN the system returns their profile information
```

### Scenario: Token Expiry
```
GIVEN an authenticated user with an expired JWT token
WHEN they request a protected endpoint
THEN the system returns 401 Unauthorized
AND the client redirects to login
```

### Scenario: Set Username for Public Profile
```
GIVEN an authenticated user without a username
WHEN they update their profile with username "johndoe"
THEN their profile becomes publicly accessible at /auth/user/johndoe
```

### Scenario: Username Uniqueness
```
GIVEN an existing user with username "johndoe"
WHEN another user attempts to set username "johndoe"
THEN the system returns an error
AND the username is not updated
```

## Security Considerations

- Passwords MUST be hashed using bcrypt
- JWT tokens SHOULD have reasonable expiration (e.g., 24 hours)
- Rate limiting SHOULD be applied to login endpoint
- Failed login attempts SHOULD be logged for security monitoring
