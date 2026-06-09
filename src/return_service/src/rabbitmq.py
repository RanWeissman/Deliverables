import json
import pika
import httpx
import time
from config import settings
from logger import get_logger

logger = get_logger("rabbitmq")

MAIN_RETURNS_QUEUE_NAME = "returns_queue"
DEAD_LETTER_QUEUE_NAME = "returns_dead_letter_queue"
MAX_RETRIES = 5

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

def process_return_event(ch, method, properties, body):
    event = json.loads(body)
    rental_id = event["rental_id"]
    car_id = event["car_id"]
    
    # Extract the number of attempts made so far from the message headers
    # Default to 0 if the header doesn't exist yet
    headers = properties.headers or {}
    retry_count = headers.get('retry_count', 0)
    
    logger.info(f"Consumer processing ReturnRequestedEvent for rental {rental_id}, car {car_id} (Attempt {retry_count + 1}/{MAX_RETRIES + 1})...")
    
    try:
        # Step 1: Finalize the Contract via Rental Service
        logger.info(f"Sending PUT to Rental Service to end rental {rental_id}")
        with httpx.Client(base_url=settings.rental_service_url) as client:
            res_rental = client.put(f"/rentals/{rental_id}/end")
            res_rental.raise_for_status()
            
        # Step 2: Update the Fleet via Vehicle Service
        logger.info(f"Sending PUT to Vehicle Service to make car {car_id} Available")
        with httpx.Client(base_url=settings.vehicle_service_url) as client:
            res_vehicle = client.put(f"/cars/{car_id}", json={
                "status": "Available",
                "expected_status": "In use"
            })
            res_vehicle.raise_for_status()
            
        logger.info(f"Successfully processed return for rental {rental_id}, car {car_id}.")
        # Final acknowledgment that completely removes the message from the queue
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logger.error(f"Error processing return {rental_id}: {str(e)}")
        
        # Retry Limit & Dead Letter Queue Mechanism
        if retry_count < MAX_RETRIES:
            logger.warning(f"Retry {retry_count + 1}/{MAX_RETRIES} for rental {rental_id}. Requeueing message...")
            
            # Increment the retry counter by 1
            headers['retry_count'] = retry_count + 1
            
            # Publish the message back to the main queue at the end of the line (to avoid blocking other messages) with the updated counter
            ch.basic_publish(
                exchange='',
                routing_key=MAIN_RETURNS_QUEUE_NAME,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                    headers=headers
                )
            )
            
            # Delete the old failed message from the head of the queue, since we already published a new copy at the back
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
            time.sleep(5) # Slight delay to prevent overload in case the other server is down
        else:
            # We reached the maximum retries! Move the message to the Dead Letter Queue (DLQ) for further manual investigation
            logger.error(f"MAX RETRIES ({MAX_RETRIES}) reached for rental {rental_id}. Moving to Dead Letter Queue (DLQ).")
            
            # Ensure the Dead Letter Queue exists
            ch.queue_declare(queue=DEAD_LETTER_QUEUE_NAME, durable=True)
            
            # Publish the failed message to the Dead Letter Queue
            ch.basic_publish(
                exchange='',
                routing_key=DEAD_LETTER_QUEUE_NAME,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                    headers=headers
                )
            )
            
            # Permanently delete the message from the main queue. It now rests in peace in the DLQ.
            ch.basic_ack(delivery_tag=method.delivery_tag)

def consume_events():
    while True:
        try:
            logger.info("Starting RabbitMQ Consumer...")
            connection = get_connection()
            channel = connection.channel()
            channel.queue_declare(queue=MAIN_RETURNS_QUEUE_NAME, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=MAIN_RETURNS_QUEUE_NAME, on_message_callback=process_return_event)
            logger.info("Waiting for messages. To exit press CTRL+C")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            logger.warning("RabbitMQ connection failed, retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Consumer encountered fatal error: {str(e)}")
            time.sleep(5)
