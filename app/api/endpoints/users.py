from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError # Import IntegrityError
import logging 

from ...core.logging import get_logger
from ...db.session import get_db
from ...api.models.user import User as DBUser 
from ...api.schemas.user import UserCreate, UserRead, UserUpdate
from ...api.dependencies.auth import get_password_hash, get_current_user

router = APIRouter()

@router.get("/me", response_model=UserRead)
async def read_users_me_route(current_user: DBUser = Depends(get_current_user)):
    """
    Fetch the current logged in user.
    """
    return current_user

@router.post("/", response_model=UserRead, responses={
    400: {"description": "User already exists"},
    403: {"description": "Not authorized to create a user"}
})
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger)
):
    """
    Creates a new user in the database.
    """

    # Checked if the user already exists
    db_user_by_username = db.query(DBUser).filter(DBUser.username == user.username).first()
    if db_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    db_user_by_email = db.query(DBUser).filter(DBUser.email == user.email).first()
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    #Hash the received password
    hashed_password = get_password_hash(user.password)

    # Create DBUser instance (excluding plain password)
    db_user = DBUser(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        # disabled defaults to False in the model
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(msg=f'User added to database: {db_user}')
    return db_user

@router.get("/{user_id}", response_model=UserRead, responses={
    404: {"description": "User not found"},
    403: {"description": "Not authorized to access this user"}
})
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger)
):
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first() # Query the database
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    logger.info(msg=f'User retrieved from database: {db_user}')
    return db_user


@router.put("/{user_id}", response_model=UserRead, responses={
    404: {"description": "User not found"},
    403: {"description": "Not authorized to update this user"},
    400: {"description": "Invalid input, e.g., username or email already registered"} # Added 400
})
async def update_user(
    user_id: int, 
    user: UserUpdate, 
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
    current_user: DBUser = Depends(get_current_user)
):
    
    # Authorization check
    if current_user.id != user_id:
        logger.warning(f"User {current_user.id} attempt to update user {user_id} forbidden.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")
    
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        logger.warning(f"Attempt to update non-existent user {user_id}.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    update_data = user.model_dump(exclude_unset=True)

    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        db_user.hashed_password = hashed_password
        # Remove password from update_data to prevent trying to set it directly if not a model field or if handled
        del update_data["password"] 
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User {user_id} updated successfully by user {current_user.id}.")
    except IntegrityError as e:
        db.rollback() # Add this line to explicitly rollback the session
        logger.warning(f"IntegrityError during user update for user {user_id}: {e.orig}")
        # Attempt to determine if it's a username or email conflict
        # This parsing can be DB-specific. A more robust way is to pre-check.
        error_detail_str = str(e.orig).lower()
        if "users_username_key" in error_detail_str or "ix_users_username" in error_detail_str:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
        elif "users_email_key" in error_detail_str or "ix_users_email" in error_detail_str:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        else:
            # Generic integrity error or other constraint violation
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user with the provided username or email may already exist, or another integrity constraint was violated.")
    return db_user

@router.delete("/{user_id}", response_model=UserRead, responses={
    404: {"description": "User not found"},
    403: {"description": "Not authorized to delete this user"}
})
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
    current_user: DBUser = Depends(get_current_user)
):
    # Authorization check
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user")
    
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Convert the SQLAlchemy model to the Pydantic model *before* deleting
    deleted_user_data = UserRead.model_validate(db_user)
    
    db.delete(db_user)
    db.commit()
    # Log the deleted user data
    logger.info(msg=f'User deleted from database: {deleted_user_data.id}')
    return deleted_user_data