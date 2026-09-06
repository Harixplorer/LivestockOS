from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.models.token_blacklist import RevokedToken
from app.schemas.auth import RegisterRequest, TokenResponse


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Retrieve user by unique email."""
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """Retrieve user by primary ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def register_user(db: AsyncSession, req: RegisterRequest) -> User:
    """Create a new farmer / user account."""
    existing = await get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    user = User(
        email=req.email.lower(),
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name,
        phone_number=req.phone_number,
        role=req.role,
        farm_name=req.farm_name or "My Farm",
        village=req.village,
        district=req.district,
        state=req.state,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str
) -> Optional[User]:
    """Validate user credentials and return user if correct."""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )
    return user


async def create_tokens_for_user(user: User) -> TokenResponse:
    """Generate access and refresh tokens for user."""
    access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "email": user.email}
    )
    refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def is_token_revoked(db: AsyncSession, token: str) -> bool:
    """Check if token is in blacklist."""
    result = await db.execute(select(RevokedToken).where(RevokedToken.token == token))
    return result.scalars().first() is not None


async def revoke_token(db: AsyncSession, token: str) -> None:
    """Add token to revocation table."""
    already_revoked = await is_token_revoked(db, token)
    if not already_revoked:
        revoked = RevokedToken(token=token)
        db.add(revoked)
        await db.commit()


async def refresh_user_tokens(db: AsyncSession, refresh_token_str: str) -> TokenResponse:
    """Validate refresh token and issue new token pair."""
    if await is_token_revoked(db, refresh_token_str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked."
        )

    payload = decode_token(refresh_token_str)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )

    user_id = payload.get("sub")
    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive."
        )

    # Invalidate old refresh token (token rotation)
    await revoke_token(db, refresh_token_str)

    return await create_tokens_for_user(user)
