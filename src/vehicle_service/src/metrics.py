from prometheus_client import Gauge

ACTIVE_CARS = Gauge(
    "active_cars_total",
    "Number of cars currently available in the fleet"
)
