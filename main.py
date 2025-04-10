from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import sys
app = FastAPI()

# Get the root logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set the minimum logging level
console_handler = logging.StreamHandler(sys.stdout)

console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

@app.get("/")
def read_root():
    return {"Hello": "World"}

# In-memory database (for demonstration purposes)
items = []

class Item(BaseModel):
    name: str
    description: str

@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    items.append(item)
    logger.info(msg=f'Item added to database: {item}')
    return item


@app.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int):
    
    if item_id < 0 or item_id >= len(items):
        raise HTTPException(status_code=404, detail="Item not found")
    
    logger.info(msg=f'Item retrieved from database: {items[item_id]}')
    return items[item_id]

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: Item):

    if item_id < 0 or item_id >= len(items):
        raise HTTPException(status_code=404, detail="Item not found")
    
    items[item_id] = item
    logger.info(msg=f'Item updated in database: {item}')
    return item

@app.delete("/items/{item_id}", response_model=Item)
async def delete_item(item_id: int):
    if item_id < 0 or item_id >= len(items):
        raise HTTPException(status_code=404, detail="Item not found")
    deleted_item = items.pop(item_id)
    logger.info(msg=f'Item deleted from database: {deleted_item}')
    return deleted_item


