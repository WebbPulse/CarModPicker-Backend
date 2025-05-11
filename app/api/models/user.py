from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from ...db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, index=True, nullable=True)
    last_name = Column(String, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    disabled = Column(Boolean, default=False, nullable=False)

    #children
    cars = relationship("Car", back_populates="user", cascade="all, delete-orphan")
