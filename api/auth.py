"""
Authentication module for AutoDesk Kiwi API.
Implements JWT-based authentication with secure password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlmodel import Field as SQLField
from sqlmodel import Session, SQLModel, select

from config import get_settings
from db import get_session
from logger import setup_logger

settings = get_settings()
logger = setup_logger("auth")

# JWT Configuration
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_expire_minutes

# Security scheme
security = HTTPBearer(auto_error=False)


# ============ Models ============

class User(SQLModel, table=True):
    """User model for authentication."""
    id: int | None = SQLField(default=None, primary_key=True)
    username: str = SQLField(unique=True, index=True, min_length=3, max_length=50)
    email: str = SQLField(unique=True, index=True)
    hashed_password: str
    is_active: bool = SQLField(default=True)
    created_at: datetime = SQLField(default_factory=lambda: datetime.now(timezone.utc))


class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    """Public user info schema."""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime


# ============ Password Utils ============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    # Bcrypt has a 72-byte limit, truncate if needed
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


# ============ JWT Utils ============

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ============ Dependencies ============

def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]
) -> User | None:
    """
    Get the current authenticated user from the JWT token.
    Returns None if no valid token is provided.
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        return None

    username: str = payload.get("sub")
    if not username:
        return None

    with get_session() as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if user and user.is_active:
            return user

    return None


def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]
) -> User:
    """
    Require authentication - raises 401 if not authenticated.
    Use this dependency for protected endpoints.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with get_session() as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )
        return user


# ============ Router ============

router = APIRouter(prefix="/auth", tags=["authentication"])
auth_limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@auth_limiter.limit("5/minute")
def register(request: Request, user_data: UserCreate):
    """Register a new user."""
    with get_session() as session:
        # Check if username exists
        existing_user = session.exec(
            select(User).where(User.username == user_data.username)
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        # Check if email exists
        existing_email = session.exec(
            select(User).where(User.email == user_data.email)
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        logger.info(f"New user registered: {user.username}")
        return user


@router.post("/login", response_model=Token)
@auth_limiter.limit("10/minute")
def login(request: Request, credentials: UserLogin):
    """Authenticate user and return JWT token."""
    with get_session() as session:
        user = session.exec(
            select(User).where(User.username == credentials.username)
        ).first()

        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )

        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        logger.info(f"User logged in: {user.username}")
        return Token(
            access_token=access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )


@router.get("/me", response_model=UserOut)
def get_me(current_user: Annotated[User, Depends(require_auth)]):
    """Get current authenticated user's info."""
    return current_user


@router.post("/logout")
def logout(current_user: Annotated[User, Depends(require_auth)]):
    """
    Logout endpoint (for client-side token invalidation).
    Note: JWT tokens are stateless, so this just confirms the logout action.
    Client should discard the token.
    """
    logger.info(f"User logged out: {current_user.username}")
    return {"message": "Successfully logged out"}
