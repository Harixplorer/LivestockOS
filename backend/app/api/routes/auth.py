from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db, security_bearer
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserResponse
from app.services.auth_service import (
    authenticate_user,
    create_tokens_for_user,
    refresh_user_tokens,
    register_user,
    revoke_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new farmer account"
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    user = await register_user(db, payload)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password"
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await create_tokens_for_user(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange refresh token for a new token pair"
)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    return await refresh_user_tokens(db, payload.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout and invalidate token"
)
async def logout(
    db: AsyncSession = Depends(get_db),
    auth_creds: HTTPAuthorizationCredentials = Security(security_bearer),
    current_user: User = Depends(get_current_user)
):
    if auth_creds and auth_creds.credentials:
        await revoke_token(db, auth_creds.credentials)
    return MessageResponse(message="Successfully logged out.")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile"
)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
