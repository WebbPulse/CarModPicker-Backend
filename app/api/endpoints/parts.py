from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging 

from ...core.logging import get_logger
from ...db.session import get_db
from ...api.models.part import Part as DBPart
from ...api.models.car import Car as DBCar
from ...api.models.user import User as DBUser
from ...api.models.build_list import BuildList as DBBuildList
from ...api.schemas.part import PartCreate, PartRead, PartUpdate
from ...api.dependencies.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=PartRead)
async def create_part(
    part: PartCreate,
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
    current_user: DBUser = Depends(get_current_user)
):
    # Verify ownership of the build list (via the car)
    db_build_list = db.query(DBBuildList).filter(DBBuildList.id == part.build_list_id).first()
    if not db_build_list:
        raise HTTPException(status_code=404, detail="Build List not found")
    if db_build_list.car.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add a part to this build list")
    
    db_part = DBPart(**part.model_dump())
    db.add(db_part)
    db.commit()
    db.refresh(db_part)
    logger.info(msg=f'part added to database: {db_part}')
    return db_part

@router.get("/{part_id}", response_model=PartRead)
async def read_part(
    part_id: int,
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
    current_user: DBUser = Depends(get_current_user)
):
    db_part = db.query(DBPart).filter(DBPart.id == part_id).first() # Query the database
    if db_part is None:
        raise HTTPException(status_code=404, detail="part not found")
    
    # Verify ownership of the build list (via the car)
    if db_part.build_list.car.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this part")

    logger.info(msg=f'part retrieved from database: {db_part}')
    return db_part

@router.put("/{part_id}", response_model=PartRead)
async def update_part(
    part_id: int, 
    part: PartUpdate, 
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
    current_user: DBUser = Depends(get_current_user)
):
    db_part = db.query(DBPart).filter(DBPart.id == part_id).first()
    if db_part is None:
        raise HTTPException(status_code=404, detail="part not found")

    # Verify ownership of the current build list (via the car)
    if db_part.build_list.car.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this part")

    update_data = part.model_dump(exclude_unset=True)

    # If build_list_id is being updated, verify ownership of the new build list
    if "build_list_id" in update_data and update_data["build_list_id"] != db_part.build_list_id:
        new_build_list_id = update_data["build_list_id"]
        db_new_build_list = db.query(DBBuildList).filter(DBBuildList.id == new_build_list_id).first()
        if not db_new_build_list:
            raise HTTPException(status_code=404, detail=f"New Build List with id {new_build_list_id} not found")
        if db_new_build_list.car.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to move part to the new build list")

    # Update model fields
    for key, value in update_data.items():
        setattr(db_part, key, value)

    db.add(db_part)
    db.commit()
    db.refresh(db_part)
    logger.info(msg=f'part updated in database: {db_part}')
    return db_part

@router.delete("/{part_id}", response_model=PartRead)
async def delete_part(
    part_id: int,
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
    current_user: DBUser = Depends(get_current_user)
):
    db_part = db.query(DBPart).filter(DBPart.id == part_id).first()
    if db_part is None:
        raise HTTPException(status_code=404, detail="part not found")

    # Verify ownership of the build list (via the car)
    if db_part.build_list.car.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this part")
    
    # Convert the SQLAlchemy model to the Pydantic model *before* deleting
    deleted_part_data = PartRead.model_validate(db_part)
    
    db.delete(db_part)
    db.commit()
    # Log the deleted part data
    logger.info(msg=f'part deleted from database: {deleted_part_data}')
    return deleted_part_data