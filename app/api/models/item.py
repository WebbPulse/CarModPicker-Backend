from sqlalchemy import Column, Integer, String
from db.base_class import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    disabled = Column(Integer, default=0)  # 0 for False, 1 for True

class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    make = Column(String, index=True)
    model = Column(String, index=True)
    year = Column(Integer, index=True)
    owner_id = Column(Integer, index=True)  # Foreign key to User table

class List(Base):
    __tablename__ = "lists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    owner_id = Column(Integer, index=True)  # Foreign key to User table