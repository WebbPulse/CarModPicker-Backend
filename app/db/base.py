# Import all the models, so that Base has them before being
# imported by Alembic
from db.base_class import Base
# POC model:
from api.models.item import Item
#actual models
from api.models.car import Car
from api.models.user import User