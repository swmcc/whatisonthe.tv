"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserPasswordUpdate,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return access token.

    Args:
        login_data: Login credentials
        db: Database session

    Returns:
        Access token and user data

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.id})

    return LoginResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User data
    """
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user profile.

    Args:
        user_update: User update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user data
    """
    # Update only provided fields
    if user_update.first_name is not None:
        current_user.first_name = user_update.first_name
    if user_update.last_name is not None:
        current_user.last_name = user_update.last_name

    await db.commit()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.post("/me/password")
async def update_password(
    password_update: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user password.

    Args:
        password_update: Password update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If current password is incorrect
    """
    # Verify current password
    if not verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    current_user.hashed_password = get_password_hash(password_update.new_password)
    await db.commit()

    return {"message": "Password updated successfully"}


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout endpoint (client should delete token).

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    return {"message": "Logged out successfully"}
