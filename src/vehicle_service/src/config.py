from utils.config import BaseServiceSettings

class Settings(BaseServiceSettings):
    service_name: str = "VehicleService"
    database_url: str


settings = Settings()
