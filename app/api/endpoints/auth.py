from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...api.models.user import User as DBUser
from ...api.schemas.user import UserRead
from ...api.dependencies.auth import verify_password, create_access_token
from ...core.config import settings

router = APIRouter()


@router.post("/token", response_model=UserRead)
async def login_for_access_token(
    response: Response,  # Inject the Response object
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticate user, set JWT token in an HTTP-only cookie, and return user details.
    Takes form data: username and password.
    """
    user = db.query(DBUser).filter(DBUser.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    access_token_data = {"sub": user.username}
    access_token = create_access_token(data=access_token_data)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # Crucial for security
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Cookie expiry in seconds
        path="/",  # Cookie available for all paths
        samesite="lax",  # Recommended for CSRF protection balance
        secure=False,  # TODO: Set to True in production if using HTTPS
    )
    return user  # Return user information


@router.post("/logout")
async def logout(response: Response):
    """
    Invalidate the user's session by clearing the access token cookie.
    """
    response.delete_cookie("access_token", path="/")
    return {"message": "Successfully logged out"}
