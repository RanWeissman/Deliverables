# Stage 5: Vehicle Service (Fleet Management) - Deep Dive

This document provides a detailed exploration of **Stage 5** from the `project_implementation_plan.md`. It explains the architecture, endpoint design, and critical concurrency protections built into the Vehicle Service.

## Overview
The Vehicle Service is the authoritative "Source of Truth" for the physical fleet. It manages the lifecycle of a car from the moment it enters the system until it is decommissioned. If another service (like the Rental Service) needs to know if a car exists or is available to drive, it must ask the Vehicle Service.

---

## 1. Core Service Features & RESTful Endpoints

To strictly fulfill the project requirements, the Vehicle Service implements the following capabilities mapped to specific synchronous FastAPI endpoints:

* **Managing vehicles (add, update, delete):**
  * `POST /cars`: Add a new car to the fleet.
  * `PUT /cars/{id}`: Update a car's details (e.g., changing its properties or correcting typos).
  * `DELETE /cars/{id}`: Delete a vehicle from the active system.

* **List all cars (with optional status filter):**
  * `GET /cars`: Retrieves the entire fleet, implementing "smart filtering" via query parameters (e.g., `?status=Available`) to dynamically search the database without pulling everything into memory.

* **Displaying each vehicle's status (available / in use / under maintenance):**
  * Both the list (`GET /cars`) and single-fetch (`GET /cars/{id}`) endpoints explicitly return the current status of the vehicle(s). The status is strictly validated to ensure it only falls into the allowed categories.

* **Check and return status / Change status:**
  * **Check & Return:** Internal services (like the Rental Service) or external clients can query `GET /cars/{id}` strictly to check if a car's returned status is "available" before proceeding with business logic.
  * **Change Status:** The `PUT /cars/{id}` endpoint is the sole mechanism to change a car's status (e.g., marking it "in use"). It utilizes atomic database updates to guarantee safety during concurrent requests.

---

## 2. Preventing Race Conditions with Atomic Updates

The most complex technical requirement in this service is handling concurrent status updates. 

* **The Problem:** Imagine a highly demanded car is `Available`. Two different users try to rent it at the exact same millisecond. If the Vehicle Service just reads the status (`Available`) and then writes the new status (`In use`), both might succeed, resulting in a double-booked car.
* **The Solution (Atomic Updates):** The `PUT /cars/{id}` endpoint must use **Atomic Database Updates** via SQLAlchemy to prevent race conditions.
  * Instead of a Read-then-Write approach, the service performs an atomic SQL `UPDATE` statement that includes the *expected* state. 
  * *Example SQL translation:* `UPDATE cars SET status = 'In use' WHERE id = 123 AND status = 'Available'`.
  * If the database reports that `0` rows were updated, it means another request beat us to it, and the service immediately returns a `409 Conflict` error, successfully preventing the double-booking.

---

## 3. A Purely Synchronous Service

Unlike the Return Service, which relies on RabbitMQ, the plan explicitly states that the Vehicle Service has **No Asynchronous Flow**.

* **Why?** The Vehicle Service is the foundational data layer. When the Rental Service needs to confirm a car is available, it needs an absolute, real-time "Yes" or "No" before it can process a customer's credit card or finalize the contract. 
* Asynchronous queues introduce latency and "eventual consistency." By keeping the Vehicle Service purely synchronous via HTTP (`httpx`), the architecture guarantees strong consistency for inventory status.

---

## 4. Observability and Quality Assurance

To ensure the service is production-ready, it must implement strict observability and testing standards:

* **Prometheus Metrics:** The FastAPI application must expose a `/metrics` endpoint. This allows the centralized Prometheus container (from Stage 3) to scrape data on how fast the `/cars` endpoints are responding and how much traffic they are handling.
* **Structured Logging:** Following the Stage 2 rules, the service logs every major action (e.g., `[VehicleService] INFO - Car 123 status changed to In use`) to both the console for Docker aggregation and to a local `app.log` file.
* **Unit Testing:** The project mandates at least 4 unit tests. The Vehicle Service is an ideal place to implement these using `pytest`. Tests should target the core logic, such as verifying that the atomic updates correctly fail when attempting to rent a car that is already `In use`.
