# Stage 4: Database Engine & Domain Models - Deep Dive

This document provides an in-depth explanation of **Stage 4** from the `project_implementation_plan.md`. It focuses on defining the core data entities for the DriveNow system and the critical architectural rule of database isolation between microservices.

## Overview
Stage 4 bridges the gap between the infrastructure (PostgreSQL) and the application code. It involves defining the exact schema (tables and columns) using SQLAlchemy ORM and establishing the fundamental rules for how data is accessed and protected across the microservices.

---

## 1. Domain Models Breakdown

Each stateful microservice is responsible for a specific domain of data. They act as the absolute "Source of Truth" for that domain.

### Vehicle Service: The Fleet
The Vehicle Service manages the physical assets. It must define a `cars` table containing at minimum:
* **`car ID`**: The primary key (e.g., UUID or integer) uniquely identifying the vehicle.
* **`model`**: The make/model of the vehicle (String).
* **`year`**: The manufacturing year (Integer).
* **`status`**: A categorical state (e.g., Enum representing `Available`, `In use`, or `Maintenance`).
* *Role:* This table is the sole source of truth regarding whether a car actually exists and if it is currently available to be driven off the lot.

### Rental Service: The Transactions
The Rental Service manages the business agreements. It must define a `rentals` table containing at minimum:
* **`rental ID`**: The primary key uniquely identifying the rental agreement.
* **`car ID`**: A reference to the vehicle being rented. 
  * *Crucial Note:* Because of database isolation (explained below), this is a "soft" foreign key. It holds the ID of a car, but there is no direct database-level foreign-key constraint tied to the `cars` table in the other service.
* **`customer name`**: The entity renting the vehicle.
* **`start date` & `end date`**: Timestamps defining the duration of the rental.
* *Role:* This table is the sole source of truth for financial history, scheduling, and ensuring no double-booking occurs for the same car on the same dates.

---

## 2. The Golden Rule: Strict Database Isolation

The most critical requirement of Stage 4 is **Database Isolation**. 

In traditional monoliths, all tables live together, and code can `JOIN` the `rentals` table with the `cars` table directly. **In this microservices architecture, that is strictly forbidden.**

* **The Rule:** No service is allowed to directly query another service's database or table.
* **Physical vs. Logical Separation:** The databases must be physically separated into entirely different PostgreSQL database files/instances, or logically separated via distinct PostgreSQL Schemas and user permissions.
* **Why is this necessary?** 
  * **Loose Coupling:** If the Vehicle Service decides to rename the `model` column to `vehicle_make_model`, or switch from PostgreSQL to MongoDB entirely, it can do so without breaking the Rental Service.
  * **Preventing Integration Databases:** If the Rental Service wants to know the `status` of a car, it cannot run `SELECT status FROM cars`. It **MUST** make an HTTP network request to the Vehicle Service's API (`GET /cars/{id}`). The API acts as the only approved contract between domains.

---

## 3. Implementation via SQLAlchemy

To execute this stage, developers will use **SQLAlchemy**:
1. **Define Models:** Create Python classes inheriting from SQLAlchemy's declarative base for `Car` and `Rental`.
2. **Schema Management:** Use SQLAlchemy engines to connect to the specific Database URL (loaded securely via Pydantic in Stage 2).
3. **Initialization:** Ensure the tables are generated in their respective, isolated PostgreSQL environments on startup (or via a migration tool like Alembic if required later in the lifecycle).
