from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging 

from core.logging import get_logger
from db.session import get_db
from api.models.item import Item as DBItem
from api.schemas.item import ItemCreate, ItemRead

router = APIRouter()

@router.post("/", response_model=ItemRead)
async def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger)
):
    db_item = DBItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    logger.info(msg=f'Item added to database: {db_item}')
    return db_item

@router.get("/{item_id}", response_model=ItemRead)
async def read_item(
    item_id: int,
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger)
):
    db_item = db.query(DBItem).filter(DBItem.id == item_id).first() # Query the database
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    logger.info(msg=f'Item retrieved from database: {db_item}')
    return db_item

@router.put("/{item_id}", response_model=ItemRead)
async def update_item(
    item_id: int, 
    item: ItemCreate, 
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger)
):
    db_item = db.query(DBItem).filter(DBItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    # Update model fields
    update_data = item.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    logger.info(msg=f'Item updated in database: {db_item}')
    return db_item

@router.delete("/{item_id}", response_model=ItemRead)
async def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    logger: logging.Logger = Depends(get_logger)
):
    db_item = db.query(DBItem).filter(DBItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Convert the SQLAlchemy model to the Pydantic model *before* deleting
    deleted_item_data = ItemRead.model_validate(db_item)
    
    db.delete(db_item)
    db.commit()
    # Log the deleted item data
    logger.info(msg=f'Item deleted from database: {deleted_item_data}')
    return deleted_item_data