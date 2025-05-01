from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.base_class import Base

class BuildList(Base):
    __tablename__ = "build_lists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, index=True, nullable=True)
    car_id = Column(Integer, ForeignKey("cars.id"), nullable=False)


    #owner
    car = relationship("Car", back_populates="build_lists")
    #children
    parts = relationship("Part", back_populates="build_list", cascade="all, delete-orphan")
    