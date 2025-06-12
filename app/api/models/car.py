from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ...db.base_class import Base


class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    make = Column(String, index=True, nullable=False)
    model = Column(String, index=True, nullable=False)
    year = Column(Integer, index=True, nullable=False)
    trim = Column(String, index=True, nullable=True)
    vin = Column(String, index=True, nullable=True)
    image_url = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # owner
    user = relationship("User", back_populates="cars")
    # children
    build_lists = relationship(
        "BuildList", back_populates="car", cascade="all, delete-orphan"
    )
