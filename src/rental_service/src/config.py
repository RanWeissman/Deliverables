from utils.config import BaseServiceSettings

class Settings(BaseServiceSettings):
    service_name: str = "RentalService"
    database_url: str
    vehicle_service_url: str


settings = Settings()
