# Stage 6: Rental Service (Transactions) - Deep Dive

This document provides a detailed exploration of **Stage 6** from the `project_implementation_plan.md`. It explains the core business logic behind registering rentals, preventing double-bookings at the database level, and managing conditional synchronous communication with the Vehicle Service.

## Overview
The Rental Service is the transactional heart of the DriveNow system. While the Vehicle Service manages the physical metal (the cars), the Rental Service manages the contracts (who has the car, and when). It is the absolute source of truth for all historical and future rental records.

---

## 1. Core Endpoints

The service exposes its capabilities via FastAPI:
* **`POST /rentals`**: The primary endpoint for booking a car. It accepts a payload containing the `car ID`, `customer name`, `start date`, and `end date`.
* **`PUT /rentals/{id}/end`**: The endpoint used to mark a specific rental agreement as completed. *(Note: This is typically called automatically by the Return Service during the return process).*

---

## 2. Pre-Check: PostgreSQL as the Final Arbiter

When a user attempts to book a car via `POST /rentals`, the service must first guarantee that the car isn't already booked for those specific dates.

* **The Problem with Application-Level Checks:** If the application runs `SELECT * FROM rentals WHERE car_id = 123 AND dates_overlap`, two concurrent requests might both see that the dates are free, resulting in a double-booking race condition.
* **The Solution (PostgreSQL Exclusion Constraints):** The architecture mandates using the database as the "Final Arbiter." By defining an **Exclusion Constraint** on the `rentals` table via SQLAlchemy, the database engine itself guarantees that no two rows for the same `car_id` can have overlapping `start_date` and `end_date` ranges.
* If a conflict occurs, PostgreSQL immediately throws an Integrity Error, which FastAPI gracefully catches and translates into a `409 Conflict` HTTP response, protecting the system flawlessly.

---

## 3. Conditional Inter-Service Communication

Because of the strict **Database Isolation** rule (Stage 4), the Rental Service cannot see the `cars` table. It must communicate with the Vehicle Service via **Synchronous HTTP Requests** (using the `httpx` library). 

However, this communication is *conditional* based on the business logic of the start date:

### Scenario A: Future Rentals (No HTTP Request)
If a user books a car starting next week, the Rental Service performs the Pre-Check (to ensure no overlap) and saves the record in its own database. 
* **Action:** It **skips** contacting the Vehicle Service entirely. 
* **Why:** The car might currently be rented by someone else today. Changing its status to "In use" today for a rental next week would corrupt the Vehicle Service's real-time accuracy.

### Scenario B: Immediate Rentals (Synchronous HTTP Request)
If a user books a car starting *today*, the Rental Service must ensure the physical car is actually sitting on the lot, ready to be driven.
* **Action:** The Rental Service uses `httpx` to make a synchronous API call to the Vehicle Service (e.g., `PUT /cars/{car_id}`).
* **The Dual-Action:** This single request asks the Vehicle Service to evaluate two things atomically: "Is the car currently `Available`? If yes, immediately change its status to `In use`."
* **Handling Failure:** If the Vehicle Service returns an error (e.g., the car is in `Maintenance`), the Rental Service rolls back its own database transaction and returns an error to the client, ensuring the two isolated databases remain logically synchronized.

---

## 4. Observability and Tracking

Given the complex nature of inter-service communication (Scenario B), observability is paramount:
* **Prometheus Metrics:** The service must track metrics like the duration of its HTTP calls to the Vehicle Service.
* **Structured Logging:** The application logs (outputting to both `stdout` and `app.log`) must explicitly trace the transaction path (e.g., `[RentalService] INFO - Created future rental 456, skipping Vehicle API call`).
