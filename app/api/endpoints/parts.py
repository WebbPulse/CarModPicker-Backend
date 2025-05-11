from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging 

from ...core.logging import get_logger
from ...db.session import get_db
from ...api.models.part import Part as DBPart
from ...api.schemas.part import PartCreate, PartRead, PartUpdate

router = APIRouter()

@router.post("/", response_model=PartRead)
async def create_part(
    part: PartCreate,
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger)
):
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
    logger: logging.Logger = Depends(get_logger)
):
    db_part = db.query(DBPart).filter(DBPart.id == part_id).first() # Query the database
    if db_part is None:
        raise HTTPException(status_code=404, detail="part not found")
    logger.info(msg=f'part retrieved from database: {db_part}')
    return db_part

@router.put("/{part_id}", response_model=PartRead)
async def update_part(
    part_id: int, 
    part: PartUpdate, 
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger)
):
    db_part = db.query(DBPart).filter(DBPart.id == part_id).first()
    if db_part is None:
        raise HTTPException(status_code=404, detail="part not found")

    # Update model fields
    update_data = part.model_dump(exclude_unset=True)
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
    logger: logging.Logger = Depends(get_logger)
):
    db_part = db.query(DBPart).filter(DBPart.id == part_id).first()
    if db_part is None:
        raise HTTPException(status_code=404, detail="part not found")
    
    # Convert the SQLAlchemy model to the Pydantic model *before* deleting
    deleted_part_data = PartRead.model_validate(db_part)
    
    db.delete(db_part)
    db.commit()
    # Log the deleted part data
    logger.info(msg=f'part deleted from database: {deleted_part_data}')
    return deleted_part_data