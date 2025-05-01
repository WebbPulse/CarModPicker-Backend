from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from db.session import get_db
from api.models.user import User as DBUser
from api.schemas.token import Token
from api.schemas.user import UserRead
from api.dependencies.auth import verify_password, create_access_token, get_current_user

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
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
         raise HTTPException(status_code=400, detail="Inactive user")

    # Data to encode in the token, 'sub' (subject) is standard for username
    access_token_data = {"sub": user.username}
    access_token = create_access_token(data=access_token_data)

    return {"access_token": access_token, "token_type": "bearer"}



@router.get("/users/me", response_model=UserRead)
async def read_users_me(current_user: DBUser = Depends(get_current_user)):
    """
    Fetch the current logged in user.
    """
    return current_user