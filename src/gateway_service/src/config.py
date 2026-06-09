from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    service_name: str = "GatewayService"
    vehicle_service_url: str
    rental_service_url: str
    return_service_url: str
    rabbitmq_uri: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
