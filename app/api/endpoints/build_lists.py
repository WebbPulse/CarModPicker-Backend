from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging 

from ...core.logging import get_logger
from ...db.session import get_db
from ...api.models.build_list import BuildList as DBBuildList
from ...api.models.car import Car as DBCar
from ...api.models.user import User as DBUser
from ...api.schemas.build_list import BuildListCreate, BuildListRead, BuildListUpdate
from ...api.dependencies.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=BuildListRead)
async def create_build_list(
    build_list: BuildListCreate,
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
    current_user: DBUser = Depends(get_current_user)
):
    # Verify car ownership
    db_car = db.query(DBCar).filter(DBCar.id == build_list.car_id).first()
    if not db_car:
        raise HTTPException(status_code=404, detail="Car not found")
    if db_car.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to create a build list for this car")

    db_build_list = DBBuildList(**build_list.model_dump())
    db.add(db_build_list)
    db.commit()
    db.refresh(db_build_list)
    logger.info(msg=f'Build List added to database: {db_build_list}')
    return db_build_list

@router.get("/{build_list_id}", response_model=BuildListRead)
async def read_build_list(
    build_list_id: int,
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
    current_user: DBUser = Depends(get_current_user)
):
    db_build_list = db.query(DBBuildList).filter(DBBuildList.id == build_list_id).first() # Query the database
    if db_build_list is None:
        raise HTTPException(status_code=404, detail="Build List not found")

    logger.info(msg=f'Build List retrieved from database: {db_build_list}')
    return db_build_list

@router.put("/{build_list_id}", response_model=BuildListRead)
async def update_build_list(
    build_list_id: int, 
    build_list: BuildListUpdate, 
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
    current_user: DBUser = Depends(get_current_user)
):
    db_build_list = db.query(DBBuildList).filter(DBBuildList.id == build_list_id).first()
    if db_build_list is None:
        raise HTTPException(status_code=404, detail="Build List not found")

    # Verify car ownership for the build list
    if db_build_list.car.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this build list")

    # If car_id is being updated, verify ownership of the new car
    update_data = build_list.model_dump(exclude_unset=True)
    if "car_id" in update_data and update_data["car_id"] != db_build_list.car_id:
        new_car_id = update_data["car_id"]
        db_new_car = db.query(DBCar).filter(DBCar.id == new_car_id).first()
        if not db_new_car:
            raise HTTPException(status_code=404, detail=f"New car with id {new_car_id} not found")
        if db_new_car.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to associate build list with the new car")

    # Update model fields
    for key, value in update_data.items():
        setattr(db_build_list, key, value)

    db.add(db_build_list)
    db.commit()
    db.refresh(db_build_list)
    logger.info(msg=f'Build List updated in database: {db_build_list}')
    return db_build_list

@router.delete("/{build_list_id}", response_model=BuildListRead)
async def delete_build_list(
    build_list_id: int,
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
    current_user: DBUser = Depends(get_current_user)
):
    db_build_list = db.query(DBBuildList).filter(DBBuildList.id == build_list_id).first()
    if db_build_list is None:
        raise HTTPException(status_code=404, detail="Build List not found")
    
    # Verify car ownership for the build list
    if db_build_list.car.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this build list")
    
    # Convert the SQLAlchemy model to the Pydantic model *before* deleting
    deleted_build_list_data = BuildListRead.model_validate(db_build_list)
    
    db.delete(db_build_list)
    db.commit()
    # Log the deleted build_list data
    logger.info(msg=f'Build List deleted from database: {deleted_build_list_data}')
    return deleted_build_list_data