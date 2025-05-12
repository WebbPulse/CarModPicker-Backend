from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging 

from ...core.logging import get_logger
from ...db.session import get_db
from ...api.models.car import Car as DBCar
from ...api.schemas.car import CarCreate, CarRead, CarUpdate
from ...api.dependencies.auth import get_current_user 
from ...api.models.user import User as DBUser 

# Helper function to get and verify car ownership
async def _verify_car_ownership(
    car_id: int,
    db: Session,
    current_user: DBUser,
    logger: logging.Logger,
    not_found_detail: str = "Car not found",
    authorization_detail: str = "Not authorized to perform this action on this car"
) -> DBCar:
    db_car = db.query(DBCar).filter(DBCar.id == car_id).first()
    if not db_car:
        logger.warning(f"Car with id {car_id} not found. User: {current_user.id}")
        raise HTTPException(status_code=404, detail=not_found_detail)
    
    if db_car.user_id != current_user.id:
        logger.warning(f"Authorization failed for car id {car_id}. User: {current_user.id}, Car Owner: {db_car.user_id}")
        raise HTTPException(status_code=403, detail=authorization_detail)
    
    return db_car

router = APIRouter()

@router.post("/", response_model=CarRead, responses={
    400: {"description": "Car already exists"},
    403: {"description": "Not authorized to create a car"}
})
async def create_car(
    car: CarCreate,
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
    current_user: DBUser = Depends(get_current_user) 
):
    db_car = DBCar(**car.model_dump(), user_id=current_user.id)
    db.add(db_car)
    db.commit()
    db.refresh(db_car)
    logger.info(msg=f'Car added to database: {db_car}')
    return db_car

@router.get("/{car_id}", response_model=CarRead, responses={
    404: {"description": "Car not found"},
    403: {"description": "Not authorized to access this car"}
})
async def read_car(
    car_id: int,
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger)
):
    
    db_car = db.query(DBCar).filter(DBCar.id == car_id).first() 
    if db_car is None:
        raise HTTPException(status_code=404, detail="Car not found")

    logger.info(msg=f'Car retrieved from database: {db_car}')
    return db_car

@router.put("/{car_id}", response_model=CarRead, responses={
    404: {"description": "Car not found"},
    403: {"description": "Not authorized to update this car"}
})
async def update_car(
    car_id: int, 
    car: CarUpdate, 
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
    current_user: DBUser = Depends(get_current_user)
):
    db_car = await _verify_car_ownership(
        car_id=car_id, 
        db=db, 
        current_user=current_user, 
        logger=logger,
        authorization_detail="Not authorized to update this car"
    )

    # Update model fields
    update_data = car.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_car, key, value)

    db.add(db_car)
    db.commit()
    db.refresh(db_car)
    logger.info(msg=f'Car updated in database: {db_car}')
    return db_car

@router.delete("/{car_id}", response_model=CarRead, responses={
    404: {"description": "Car not found"},
    403: {"description": "Not authorized to delete this car"}
})
async def delete_car(
    car_id: int,
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
    current_user: DBUser = Depends(get_current_user) 
):
    db_car = await _verify_car_ownership(
        car_id=car_id,
        db=db,
        current_user=current_user,
        logger=logger,
        authorization_detail="Not authorized to delete this car"
    )
    
    # Convert the SQLAlchemy model to the Pydantic model *before* deleting
    deleted_car_data = CarRead.model_validate(db_car)
    
    db.delete(db_car)
    db.commit()
    # Log the deleted car data
    logger.info(msg=f'car deleted from database: {deleted_car_data}')
    return deleted_car_data