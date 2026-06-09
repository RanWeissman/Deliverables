from prometheus_client import Gauge

ONGOING_RENTALS = Gauge(
    "ongoing_rentals_total",
    "Number of currently active rentals"
)
