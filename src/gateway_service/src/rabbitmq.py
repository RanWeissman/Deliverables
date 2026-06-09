import json
import pika
from config import settings
from utils.logger import get_logger
from config import settings

logger = get_logger(settings.service_name, "rabbitmq")

MAIN_RETURNS_QUEUE_NAME = "returns_queue"

def get_connection():
    parameters = pika.URLParameters(settings.rabbitmq_uri)
    return pika.BlockingConnection(parameters)

def publish_event(rental_id: int, car_id: int):
    try:
        connection = get_connection()
        channel = connection.channel()
        channel.queue_declare(queue=MAIN_RETURNS_QUEUE_NAME, durable=True)
        
        message = json.dumps({"rental_id": rental_id, "car_id": car_id})
        
        # When publishing for the first time, we set retry_count to 0
        channel.basic_publish(
            exchange='',
            routing_key=MAIN_RETURNS_QUEUE_NAME,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                headers={'retry_count': 0}
            )
        )
        logger.info(f"Published ReturnRequestedEvent for rental {rental_id}, car {car_id}")
        connection.close()
    except Exception as e:
        logger.error(f"Failed to publish message: {str(e)}")
        raise
