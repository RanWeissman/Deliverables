# Return Service Architecture Change

## Background
We are redesigning the architecture for the Return Service to improve scalability, fault tolerance, and performance. The goal is to move from a synchronous communication model to an asynchronous, event-driven model using a Message Queue (MQ).

## Proposed Architecture

### 1. API Gateway (Producer)
Instead of calling the Return Service directly and waiting for a response, the API Gateway will now act as a message producer.
* **Action:** When a return request is received, the Gateway will validate the basic request and immediately publish a message containing the return details to a dedicated Message Queue.
* **Response:** The Gateway will respond to the client immediately (e.g., `HTTP 202 Accepted`), improving the response time and not blocking the client while the return is being processed.

### 2. Message Queue (MQ)
The Message Queue will act as a buffer and a reliable transport layer between the Gateway and the Return Service.
* It will hold the return requests until the Return Service is ready to process them.

### 3. Return Service (Consumer)
The Return Service will no longer receive direct HTTP traffic from the Gateway for processing returns. Instead, it will act as an MQ consumer.
* **Action:** It will continuously poll/listen to the MQ for new return messages.
* **Processing:** Once a message (containing `rental_id` and `car_id`) is pulled, the Return Service executes the exact existing business logic:
    1. **Finalize Contract:** Sends a `PUT` request to the Rental Service (`/rentals/{rental_id}/end`) to officially end the rental.
    2. **Update Fleet:** Sends a `PUT` request to the Vehicle Service (`/cars/{car_id}`) to change the car's status to `Available` (from expected `In use`).
* **ACK & Error Handling Logic:**
    * **Success:** If both steps succeed, it sends an `ACK` to permanently remove the message from the queue.
    * **Failure & Retries:** If an error occurs (e.g., a service is down), it increments a `retry_count`. If below the limit (Max 5), it republishes the message to the back of the main queue with the updated count, `ACK`s the old message, and waits 5 seconds.
    * **Dead Letter Queue (DLQ):** If the message fails 5 times, it is published to a Dead Letter Queue (`returns_dead_letter_queue`) for manual investigation, and the old message is `ACK`ed to remove it from the main queue.

## Advantages of this Architecture
1. **Decoupling:** The API Gateway and Return Service are decoupled.
2. **Resilience & Fault Tolerance:** If the Return Service is temporarily down, the API Gateway can still accept return requests. The messages will safely wait in the queue until the Return Service is back online.
3. **Load Leveling (Buffering):** During high traffic spikes, the MQ will absorb the load, preventing the Return Service from being overwhelmed. The service will process messages at its own pace.

## Open Questions / Next Steps
* **Technology Choice:** Which MQ system should we use? (e.g., RabbitMQ, Kafka, AWS SQS, Redis).
* **Message Payload Contract:** Define the exact JSON structure of the message passed from the Gateway to the MQ.
* **Saga / Rollback Handling:** How do we handle partial failures when communicating with other services during the return process?
* **DLQ (Dead Letter Queue):** Define the retry policy and what happens to messages that fail processing multiple times.
