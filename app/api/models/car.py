from sqlalchemy import Column, Integer, String, ForeignKey
from db.base_class import Base

class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    make = Column(String, index=True)
    model = Column(String, index=True)
    year = Column(Integer, index=True)

    