from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import logging
import sys
from core.config import settings
from sqlalchemy.orm import Session
from db.session import get_db, engine
from db.base import Base  # Import Base for table creation
from api.models.item import Item as DBItem
from api.schemas.item import ItemCreate, ItemRead

# Create database tables (For PoC, use Alembic for production)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG
)

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/items/", response_model=ItemRead) # Use ItemRead schema
async def create_item(item: ItemCreate, db: Session = Depends(get_db)): # Use ItemCreate schema and inject db session
    
    db_item = DBItem(**item.model_dump())  # Create SQLAlchemy model instance
    db.add(db_item)
    db.commit() 
    db.refresh(db_item)
    logger.info(msg=f'Item added to database: {db_item}')
    return db_item


@app.get("/items/{item_id}", response_model=ItemRead)
async def read_item(item_id: int, db: Session = Depends(get_db)):
    
    db_item = db.query(DBItem).filter(DBItem.id == item_id).first() # Query the database
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    logger.info(msg=f'Item retrieved from database: {db_item}')
    return db_item

@app.put("/items/{item_id}", response_model=ItemRead) # Use ItemRead schema
async def update_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)): # Use ItemCreate schema and inject db session
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

@app.delete("/items/{item_id}", response_model=ItemRead) # Use ItemRead schema
async def delete_item(item_id: int, db: Session = Depends(get_db)): # Inject db session
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
    


