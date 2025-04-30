from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from db.session import get_db
from api.models.user import User as DBUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Scheme
# tokenUrl should point to your login endpoint (we'll create this later)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Password Utilities ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

# --- JWT Utilities ---

ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Use default expiration from settings
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- Pydantic Schemas for Token ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# --- Dependency to Get Current User ---

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> DBUser:
    """Decodes JWT token, validates credentials, and returns the user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = db.query(DBUser).filter(DBUser.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    # Add checks here if needed (e.g., user.disabled)
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user



# --- Dependency for Optional Current User (if needed for public endpoints) ---
async def get_current_active_user_optional(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Optional[DBUser]:
    if not token:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        # If token is invalid/expired but present, treat as unauthenticated
        return None

