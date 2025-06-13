from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ...db.base_class import Base


class BrakeRotor(Base):
    __tablename__ = "brake_rotors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    part_type = Column(String, index=True, nullable=True)
    part_number = Column(String, index=True, nullable=True)
    manufacturer = Column(String, index=True, nullable=True)
    material = Column(String, index=True, nullable=True)
    description = Column(String, index=True, nullable=True)
    price = Column(Integer, index=True, nullable=True)
    image_url = Column(String, nullable=True)

    build_list_id = Column(Integer, ForeignKey("build_lists.id"), nullable=False)

    # owner
    build_list = relationship("BuildList", back_populates="brake_rotors")
