# Architecture Design: DriveNow Vehicle Management System

This document outlines the unified and final system architecture for the DriveNow internal vehicle management system. The architecture is designed as a highly scalable microservices environment, utilizing a combination of synchronous HTTP requests and asynchronous event-driven communication via a Message Queue. It strictly follows the technical requirements of the `N-EXERCISE.md` specification, adhering perfectly to SOLID principles and Separation of Concerns.

---

## 1. System Services (Microservices)

The system is composed of 4 distinct services running as separate Docker containers:

### 1. Main Service / API Gateway
It serves as the Single Entry Point to the system.
* **Workers**: **Multiple**. As a completely stateless proxy, it can be horizontally scaled without any data conflicts.
* **Role**: Exposes the API (or CLI) outward, receives all requests from the user, and routes them to the appropriate backend service (`Rentals`, `Returns`, `Cars`).
* **Database / Tables Needed**: **None**. It does not hold its own database and relies entirely on downstream services.
* **Logging & Metrics**: Every service will have logging and metrics. This gateway implements Prometheus metrics to measure the average response time of requests in the system end-to-end, and uses structured logging to console and file.

### 2. Vehicle Service
Exclusively responsible for Fleet Management.
* **Workers**: **Multiple**. PostgreSQL's row-level locking handles concurrent updates safely, allowing multiple Vehicle Service instances to process requests simultaneously without blocking each other.
* **Database / Tables Needed**: **PostgreSQL** — requires the `cars` table (car ID, model, year, status). **No other service touches this table directly.**
* **Synchronous Flow (APIs)**: The service exposes synchronous HTTP endpoints to:
  - Check all available cars in the system.
  - Check the status of a specific car (Available / In use).
  - Update/Change car status to "In use" (synchronously for the rental process). **This MUST still be implemented as an Atomic Update (`UPDATE cars SET status='In use' WHERE id=X AND status='Available'`) even with PostgreSQL. This ensures thread-safety between concurrent workers trying to rent the exact same car at the exact same microsecond, preventing race conditions.**
  - Update/Change car status to "Available" (for the return process).
* **Logging & Metrics**: Every service will have logging and metrics. This service implements Prometheus metrics and structured logging (console and file).

### 3. Rental Service
The business heart that manages the lifecycle of new rental transactions.
* **Workers**: **Multiple**. PostgreSQL handles concurrent inserts gracefully. Furthermore, database-level constraints (e.g., Exclusion Constraints on date ranges) natively prevent overlapping bookings, allowing this service to safely run multiple workers.
* **Database / Tables Needed**: **PostgreSQL** — requires the `rentals` table (rental ID, car ID, customer name, start date, end date).
* **Role**: Exposes an API to register a car rental.
* **Synchronous Flow (Linear Logic)**:
  1. **Pre-check**: The service queries its own `rentals` table to **check there is no other rental for this car in this time period**.
  2. **Conditional Atomic Reserve**: If the dates are clear, the service checks the requested `start_date`:
     * **If the rental starts TODAY (Immediate):** The service makes a **single synchronous API call** to the Vehicle Service to *both* check current availability and update the status to "In use" atomically. It waits for the response to see if it succeeded.
     * **If the rental starts in the FUTURE:** The service skips the Vehicle Service API call entirely (since current real-time status doesn't matter for future bookings).
  3. **Write**: If the previous steps succeed, the service proceeds to write the rental transaction to its own internal DB (`rentals` table).
  4. **Failure Handling**: If any step in this process stops or fails (e.g., overlapping dates found, Vehicle Service is down for immediate rentals, or atomic update fails), the process halts immediately and the service sends a failure response to the client.
* **Future Rental Race Condition (TOCTOU) & Prevention**: 
  * **The Problem**: A "Time-of-Check to Time-of-Use" race condition occurs if Worker A and Worker B both check the `rentals` table for the same future dates simultaneously. Both workers see the dates are clear, and both insert a rental record, resulting in a double-booking.
  * **The Solution**: Application-level checks are not enough. We solve this at the database engine level using **PostgreSQL Exclusion Constraints**. We define a strict rule: *No two rows can have the same `car_id` if their `start_date` and `end_date` ranges overlap.* If two workers try to insert at the exact same microsecond, PostgreSQL will save the first one and forcefully reject the second with an `IntegrityError`, completely eliminating the race condition.
* **Logging & Metrics**: Every service will have logging and metrics. This service implements Prometheus metrics and structured logging (console and file).

### 4. Return Service
Manages the termination of rentals and returning cars to the fleet.
* **Workers**: **Multiple**. Following the "competing consumers" pattern, multiple workers can listen to the RabbitMQ queue. RabbitMQ ensures each return message is processed by exactly one worker, allowing high throughput.
* **Database / Tables Needed**: **None natively**. It needs a connection to RabbitMQ to consume messages, but does not own a database table.
* **Role**: Processes car returns asynchronously via a queue.
* **Communication (MQ Consumer & Sync HTTP)**: This service acts as a Consumer that listens to the Message Queue for `ReturnRequestedEvent`s. When an event is consumed, it makes a **synchronous API call** to the Vehicle Service to update the car's status to "Available".
* **Logging & Metrics**: Every service will have logging and metrics. This service implements Prometheus metrics and structured logging (console and file).

---

## 2. Complementary Infrastructure (Docker Compose)

All these services run side-by-side and are orchestrated using a single command via the `docker-compose.yml` file, which includes the following infrastructural components:

* **Database (PostgreSQL)**: We use PostgreSQL running as a dedicated container.
  * **Why SQL and not NoSQL?** The system manages financial/business transactions (like car rentals) which require strict ACID compliance to guarantee absolute data integrity. Our data is highly structured with clear, relational schemas (e.g., cars and their rentals). NoSQL is great for unstructured data or document storage, but SQL databases enforce rigid schemas, ensuring our core business rules are fundamentally protected at the database level.
  * **Why PostgreSQL specifically?** PostgreSQL is an enterprise-grade SQL database that perfectly supports high concurrency through row-level locking. It eliminates the file-locking bottlenecks of simpler databases like SQLite, allowing all our microservices to safely run multiple workers simultaneously. It also offers advanced features like Exclusion Constraints to natively prevent overlapping rental dates at the engine level.
* **Message Queue Container**: A broker like RabbitMQ, which manages the queues for return requests consumed by the Return Service.
* **Prometheus Container**: Pulls metrics from the Main Service and other services to allow data visualization (e.g., via Grafana). This fulfills the metrics requirement and enables comprehensive monitoring.

---

## 3. The Golden Rule: Internal DB vs. External Communication

To ensure data integrity and avoid tight coupling, the architecture enforces a strict communication rule:

* **NO Direct DB Access**: A service **MUST NEVER** access another service's database directly. 
* **Synchronous Updates**: When absolute certainty is needed before a transaction (like creating a rental), services communicate synchronously via HTTP REST calls.
* **Asynchronous Notifications**: For side-effects (like returning a car), services use the Message Queue to publish events, ensuring decoupled and fast responses.

---

## 4. Logging & Dependency Management

* **Logging**: There is no dedicated logging service. Instead, each microservice uses Python's built-in `logging` module configured with dual handlers. It outputs formatted logs to the console (`stdout`) AND writes them directly to a physical `app.log` file (which can be persisted via Docker volumes). This strictly fulfills the assignment requirement to log to both console and file, while still allowing Docker Compose to aggregate the console output.
* **Independent Dependencies**: Each microservice directory (`gateway_service/`, `vehicle_service/`, `rental_service/`, `return_service/`) contains its own dedicated `pyproject.toml` and `poetry.lock` file.
* **Benefits**: Prevents *Dependency Hell*, ensures fast build times, and guarantees that upgrading a package in one service does not unintentionally break another service.

---

## 5. High-Level Flow Diagram

```mermaid
graph TD
    Client[Client / Postman] -->|HTTP Request| API[1. API Gateway / Main Service]
    
    API -->|Route: /rentals| RentalSvc[3. Rental Service]
    API -->|Route: /returns| ReturnSvc[4. Return Service]
    API -->|Route: /cars| VehicleSvc[2. Vehicle Service]
    
    RentalSvc -->|1. Internal Check Overlap Dates| RentalDB[(Rentals Table)]
    RentalSvc -->|2. [If Today] Sync Atomic Reserve| VehicleSvc
    
    RentalSvc -->|3. Write Transaction| RentalDB[(Rentals Table)]
    VehicleSvc -->|Read/Write| VehicleDB[(Cars Table)]
    
    MQ[Message Queue: RabbitMQ] -.->|Consume Event: ReturnRequested| ReturnSvc
    
    ReturnSvc -->|Sync Update to 'Available'| VehicleSvc
    
    Prometheus[(Prometheus Container)] -->|Scrape Metrics| API
    Prometheus -->|Scrape Metrics| VehicleSvc
    Prometheus -->|Scrape Metrics| RentalSvc
    Prometheus -->|Scrape Metrics| ReturnSvc
```

This streamlined microservices architecture removes unnecessary middlemen, keeps the infrastructure lightweight, and answers all requirements for a robust, event-driven system capable of extensive future expansion.
