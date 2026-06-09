from sqlalchemy import Column, Integer, String, DateTime, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from .database import Base, engine
from config import settings

class Rental(Base):
    __tablename__ = "rentals"

    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, index=True, nullable=False)  # Soft foreign key to Vehicle Service
    customer_name = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Conditionally apply the ExclusionConstraint if we are NOT using SQLite
    # This allows us to use an in-memory SQLite DB for fast unit tests.
    if not settings.database_url.startswith("sqlite"):
        __table_args__ = (
            ExcludeConstraint(
                ('car_id', '='),
                (text('tsrange(start_date, end_date)'), '&&'),
                name='no_overlapping_rentals',
                using='gist'
            ),
        )

# Auto-generate schema (for the purposes of this stage)
Base.metadata.create_all(bind=engine)
