# Import all the models, so that Base has them before being
# imported by Alembic
from db.base_class import Base
# Import your models here:
from api.models.item import Item