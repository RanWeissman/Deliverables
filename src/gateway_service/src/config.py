from utils.config import BaseServiceSettings

class Settings(BaseServiceSettings):
    service_name: str = "GatewayService"
    vehicle_service_url: str
    rental_service_url: str
    return_service_url: str
    rabbitmq_uri: str


settings = Settings()
