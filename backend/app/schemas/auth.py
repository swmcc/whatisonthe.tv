"""Authentication schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)


class UserPasswordUpdate(BaseModel):
    """Schema for updating user password."""

    current_password: str = Field(..., min_length=6, max_length=100)
    new_password: str = Field(..., min_length=6, max_length=100)


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response schema."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
