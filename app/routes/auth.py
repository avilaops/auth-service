"""Authentication routes"""
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from datetime import datetime, timedelta
from ..database import get_database, get_redis
from ..models import (
    UserRegister, UserLogin, UserResponse, Token,
    PasswordReset, PasswordResetConfirm, TokenRefresh
)
from ..security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, decode_token, generate_verification_token,
    generate_reset_token
)
from ..email import send_verification_email, send_password_reset_email
from ..config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister, background_tasks: BackgroundTasks):
    """Register new user"""
    db = get_database()

    # Check if user exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user_dict = {
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": get_password_hash(user.password),
        "is_active": True,
        "is_verified": False,
        "created_at": datetime.utcnow()
    }

    result = await db.users.insert_one(user_dict)

    # Generate verification token
    verification_token = generate_verification_token()

    # Store token in Redis (expires in 24 hours)
    redis_client = get_redis()
    await redis_client.setex(
        f"verification:{verification_token}",
        86400,  # 24 hours
        user.email
    )

    # Send verification email
    background_tasks.add_task(send_verification_email, user.email, verification_token)

    return {
        "message": "User registered successfully. Please check your email to verify your account.",
        "user_id": str(result.inserted_id)
    }


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login user"""
    db = get_database()

    # Find user
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Create tokens
    token_data = {"sub": user["email"], "user_id": str(user["_id"])}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Store refresh token in Redis
    redis_client = get_redis()
    await redis_client.setex(
        f"refresh_token:{user['email']}",
        settings.REFRESH_TOKEN_EXPIRATION,
        refresh_token
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_EXPIRATION
    )


@router.post("/verify-email")
async def verify_email(token: str):
    """Verify user email"""
    redis_client = get_redis()

    # Get email from token
    email = await redis_client.get(f"verification:{token}")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    # Update user
    db = get_database()
    result = await db.users.update_one(
        {"email": email},
        {"$set": {"is_verified": True, "updated_at": datetime.utcnow()}}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Delete token
    await redis_client.delete(f"verification:{token}")

    return {"message": "Email verified successfully"}


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh):
    """Refresh access token"""
    payload = decode_token(token_data.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    email = payload.get("sub")

    # Verify refresh token exists in Redis
    redis_client = get_redis()
    stored_token = await redis_client.get(f"refresh_token:{email}")

    if not stored_token or stored_token != token_data.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or expired"
        )

    # Create new access token
    new_token_data = {"sub": email, "user_id": payload.get("user_id")}
    access_token = create_access_token(new_token_data)

    return Token(
        access_token=access_token,
        refresh_token=token_data.refresh_token,
        expires_in=settings.JWT_EXPIRATION
    )


@router.post("/password-reset")
async def request_password_reset(data: PasswordReset, background_tasks: BackgroundTasks):
    """Request password reset"""
    db = get_database()

    # Check if user exists
    user = await db.users.find_one({"email": data.email})
    if not user:
        # Don't reveal if user exists or not
        return {"message": "If the email exists, a password reset link has been sent"}

    # Generate reset token
    reset_token = generate_reset_token()

    # Store token in Redis (expires in 1 hour)
    redis_client = get_redis()
    await redis_client.setex(
        f"password_reset:{reset_token}",
        3600,  # 1 hour
        data.email
    )

    # Send reset email
    background_tasks.add_task(send_password_reset_email, data.email, reset_token)

    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(data: PasswordResetConfirm):
    """Confirm password reset"""
    redis_client = get_redis()

    # Get email from token
    email = await redis_client.get(f"password_reset:{data.token}")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Update password
    db = get_database()
    result = await db.users.update_one(
        {"email": email},
        {
            "$set": {
                "hashed_password": get_password_hash(data.new_password),
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Delete token and refresh tokens
    await redis_client.delete(f"password_reset:{data.token}")
    await redis_client.delete(f"refresh_token:{email}")

    return {"message": "Password reset successfully"}


@router.post("/logout")
async def logout(email: str):
    """Logout user"""
    redis_client = get_redis()

    # Delete refresh token
    await redis_client.delete(f"refresh_token:{email}")

    return {"message": "Logged out successfully"}
