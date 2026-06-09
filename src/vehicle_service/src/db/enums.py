import enum

class CarStatus(str, enum.Enum):
    AVAILABLE = "Available"
    IN_USE = "In use"
    MAINTENANCE = "Maintenance"
