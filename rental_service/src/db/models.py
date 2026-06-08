from sqlalchemy import Column, Integer, String, DateTime
from .database import Base, engine

class Rental(Base):
    __tablename__ = "rentals"

    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, index=True, nullable=False)  # Soft foreign key to Vehicle Service
    customer_name = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

# Auto-generate schema (for the purposes of this stage)
Base.metadata.create_all(bind=engine)
