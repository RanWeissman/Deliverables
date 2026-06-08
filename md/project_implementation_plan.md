# Deep Implementation Plan: DriveNow Microservices Architecture

This document provides a rigid, highly detailed implementation plan for the DriveNow system based on a **4-Service Microservices and Event-Driven Architecture**. To ensure the requirements are strictly met, every stage below outlines **Strict Technical Requirements**, including exact details on **Synchronous (HTTP)** vs. **Asynchronous (Event-Driven)** communication.

---

## Stage 1: Monorepo Structure & Dependency Management
**Goal:** Create the project skeleton for 4 separate services and enforce strict environment controls.
* **Architecture Style:** Polyrepo containing isolated microservices.
* **Strict Requirements:**
  * Must use Python 3.14.5.
  * Use **uv** for dependency management (replacing Poetry). Each service must be managed using uv (e.g., `uv init`) and have its own `pyproject.toml`.
  * Required dependencies: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `pytest`, `pydantic-settings`, `httpx` (for synchronous inter-service HTTP calls), and `pika` / `aio-pika` (for asynchronous RabbitMQ messaging).
* **Tasks:** 
  * Initialize the monorepo structure with distinct directories: `gateway_service`, `vehicle_service`, `rental_service`, and `return_service`.
  * Initialize a Git repository.
  * Add a comprehensive `.gitignore` file to ignore environment files, `__pycache__`, etc.

## Stage 2: Shared Core Configuration & Logging Setup
**Goal:** Establish environment variables and observability defaults tailored for distributed services.
* **Strict Requirements:**
  * **No hardcoded configurations.** Database URLs and RabbitMQ credentials MUST be loaded using Pydantic V2 `BaseSettings`.
  * **Logging:** There is NO dedicated logging worker. Each service must instantiate its own logger using the Python `logging` module, explicitly naming the service (e.g., `[VehicleService]`). The logger MUST be configured with dual handlers: one outputting to `stdout` (so Docker Compose can aggregate it), and one writing to a physical `app.log` file, directly fulfilling the exercise requirement.

## Stage 3: Infrastructure Orchestration (docker-compose)
**Goal:** Stand up the backing services (Databases, Message Queue, Metrics).
* **Strict Requirements:**
  * Must create `docker-compose.yml` containing:
    - **PostgreSQL** container to act as the primary database. It handles concurrent connections flawlessly with row-level locking, allowing all services to scale their workers horizontally without file-locking bottlenecks.
    - **RabbitMQ** container for **Asynchronous** event-driven communication.
    - **Prometheus** container to scrape metrics synchronously from our 4 services.
* **Tasks:** Define the internal Docker bridge network (`drivenow_net`), volumes for data persistence, and expose necessary ports.

## Stage 4: Database Engine & Domain Models
**Goal:** Connect the specific services to their isolated databases and define Data Entities.
* **Strict Requirements:**
  * **Vehicle Service** MUST define the `cars` table (car ID, model, year, status).
  * **Rental Service** MUST define the `rentals` table (rental ID, car ID, customer name, start date, end date).
  * **Database Isolation:** The databases are physically separated (or logically separated via distinct schemas). No service is allowed to query the other service's table directly. This enforces strict Microservice boundaries.

## Stage 5: Vehicle Service (Fleet Management)
**Goal:** Implement the logic for managing cars.
* **Synchronous Flow:**
  * Creates FastAPI endpoints (`POST /cars`, `GET /cars`, `GET /cars/{id}`, `PUT /cars/{id}`, `DELETE /cars/{id}`) to handle synchronous fleet management requests, covering adding, updating, deleting, and listing cars with optional status filters.
  * Status updates (e.g., to "In use" or "Available") are handled via `PUT /cars/{id}` or specific status endpoints with atomic database updates to prevent race conditions.
* **Asynchronous Flow:**
  * None. This service operates purely synchronously as the source of truth for fleet status.
* **Logging & Metrics:**
  * Every service will have logging and metrics. This service implements Prometheus metrics and structured logging (console and file). Include at least 4 unit tests across the project.

## Stage 6: Rental Service (Transactions)
**Goal:** Implement the core business logic for rentals.
* **Synchronous Flow:**
  * Creates FastAPI endpoints (`POST /rentals`, `PUT /rentals/{id}/end`) for registering and ending rentals.
  * **Pre-Check (Database Final Arbiter):** Before creating a rental, the Rental Service MUST perform a check against its *own* `rentals` database to guarantee there are no overlapping rental time periods for this car, utilizing PostgreSQL Exclusion Constraints.
  * **Conditional Inter-Service Communication:** If dates are clear, the service evaluates the start date:
    * **If today (Immediate):** It MUST make a single **Synchronous HTTP Request** (using `httpx`) to the Vehicle Service to *both* verify the car is `Available` and update its status to `In use` atomically, waiting for confirmation.
    * **If future:** It skips the Vehicle Service request entirely.
* **Asynchronous Flow:**
  * None inherently required for creation, but serves as the source of truth for rental records.
* **Logging & Metrics:**
  * Every service will have logging and metrics. This service implements Prometheus metrics and structured logging (console and file).

## Stage 7: Return Service (Asynchronous Processing)
**Goal:** Manages the termination of rentals and returning cars to the fleet asynchronously.
* **Synchronous Flow (Producer):**
  * Exposes a FastAPI endpoint (`POST /returns`) that receives a return request, instantly publishes a `ReturnRequestedEvent` to RabbitMQ, and returns a 202 Accepted response to the client.
* **Asynchronous Flow (Consumer):**
  * Implements an asynchronous RabbitMQ Consumer that listens to the return queue.
  * When a `ReturnRequestedEvent` is consumed, it MUST make **Synchronous HTTP Requests** (using `httpx`) to:
    1. **Rental Service:** To mark the rental record as ended (`PUT /rentals/{id}/end`).
    2. **Vehicle Service:** To update the car's status to `Available` (`PUT /cars/{car_id}`).
* **Logging & Metrics:**
  * Every service will have logging and metrics. This service implements Prometheus metrics and structured logging (console and file).

## Stage 8: Main Service / API Gateway
**Goal:** Create the single entry point for the system.
* **Synchronous Flow:**
  * Exposes the external REST API to the client.
  * Uses **Synchronous HTTP proxying** to route `/cars` requests to the Vehicle Service, `/rentals` requests to the Rental Service, and `/returns` requests to the Return Service.
* **Strict Requirements:**
  * Does NOT hold a database.
  * **Logging & Metrics:** Every service will have logging and metrics. This gateway implements Prometheus Metrics via Middleware. Tracks the `Average response time` of all synchronous requests passing through the gateway, and uses structured logging to console and file.

## Stage 9: Containerization of Services
**Goal:** Ensure all custom services run inside Docker natively.
* **Strict Requirements:**
  * Write a `Dockerfile` for each of the 4 services.
  * Add the 4 services to the `docker-compose.yml`, configuring `depends_on` so they wait for RabbitMQ to be healthy before starting. 

## Stage 10: Final Documentation & Review
**Goal:** Produce the required deliverables.
* **Strict Requirements:**
  * `README.md` must contain exactly what `N-EXERCISE.md` demands: Graphic flow diagram (from the architecture doc), run instructions (`docker-compose up`), API usage examples, and architecture description.
  * Include Screenshots of the Prometheus dashboard and the centralized Docker logs (`docker-compose logs`) demonstrating the asynchronous events in action.
