from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging 

from core.logging import get_logger
from db.session import get_db
from api.models.build_list import BuildList as DBBuildList
# need to adjust
from api.schemas.item import ItemCreate, ItemRead