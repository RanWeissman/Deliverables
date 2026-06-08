from sqlalchemy import Column, Integer, String, Enum
from .database import Base, engine
from .enums import CarStatus

class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    model = Column(String, index=True, nullable=False)
    year = Column(Integer, nullable=False)
    status = Column(Enum(CarStatus), default=CarStatus.AVAILABLE, nullable=False)

# Auto-generate schema (for the purposes of this stage)
Base.metadata.create_all(bind=engine)
