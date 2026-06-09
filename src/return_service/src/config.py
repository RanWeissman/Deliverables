from utils.config import BaseServiceSettings

class Settings(BaseServiceSettings):
    service_name: str = "ReturnService"
    rabbitmq_uri: str
    rental_service_url: str
    vehicle_service_url: str


settings = Settings()
