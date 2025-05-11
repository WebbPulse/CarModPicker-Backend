from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging 

from ...core.logging import get_logger
from ...db.session import get_db
from ...api.models.user import User as DBUser 
from ...api.schemas.user import UserCreate, UserRead, UserUpdate
from ...api.dependencies.auth import get_password_hash, get_current_user

router = APIRouter()

@router.post("/", response_model=UserRead)
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

@router.get("/{user_id}", response_model=UserRead)
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


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int, 
    user: UserUpdate, 
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
    current_user: DBUser = Depends(get_current_user)
):
    
    # Authorization check
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")
    
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update model fields
    if user.username is not None:
        db_user.username = user.username
    if user.email is not None:
        db_user.email = user.email
    if user.first_name is not None:
        db_user.first_name = user.first_name
    if user.last_name is not None:
        db_user.last_name = user.last_name
    if user.disabled is not None:
        db_user.disabled = user.disabled
    if user.password is not None:
        #Hash the received password
        hashed_password = get_password_hash(user.password)
        db_user.hashed_password = hashed_password

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(msg=f'User updated in database: {db_user}')
    return db_user

@router.delete("/{user_id}", response_model=UserRead)
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