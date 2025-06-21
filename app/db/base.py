# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base

# actual models
from app.api.models.user import User
from app.api.models.car import Car
from app.api.models.build_list import BuildList
from app.api.models.part import Part
