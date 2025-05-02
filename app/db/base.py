# Import all the models, so that Base has them before being
# imported by Alembic
from ..db.base_class import Base
#actual models
from ..api.models.user import User
from ..api.models.car import Car
from ..api.models.build_list import BuildList
from ..api.models.part import Part