# Stage 2: Shared Core Configuration & Logging Setup - Deep Dive

This document provides a detailed exploration of **Stage 2** from the `project_implementation_plan.md`. It explains the strict requirements surrounding environment-driven configuration and the decentralized logging strategy required for the DriveNow microservices architecture.

## Overview
In a distributed architecture, services must be resilient, portable, and easily traceable. Stage 2 enforces two fundamental patterns to achieve this: strict environment variable injection for configuration, and a standardized, dual-output logging mechanism per service.

---

## 1. Strict Configuration via Pydantic V2 (`BaseSettings`)

The primary rule for configuration is: **Absolutely no hardcoded credentials or environment-specific URLs within the application code.**

* **The Problem:** Hardcoding values like a PostgreSQL connection string or RabbitMQ host ties the codebase to a specific environment (e.g., local development). This breaks the core principle of containerized microservices.
* **The Solution (`pydantic-settings`):** Every service must use Pydantic V2's `BaseSettings` class to define its expected configuration. 
  * Developers define a `Settings` class (e.g., in a `config.py` file) that declares expected environment variables like `DATABASE_URL` or `RABBITMQ_URI` with expected data types.
  * **Fail-Fast Boot:** When the service boots up, Pydantic immediately reads the environment variables. If a required variable is missing or formatted incorrectly, the service throws a validation error and refuses to start. This "fail-fast" behavior prevents silent failures later in the application lifecycle.

---

## 2. Decentralized, Service-Specific Logging

Unlike some monolithic setups or external observability stacks, this architecture dictates that **there is no dedicated logging worker or sidecar**. Each microservice is entirely responsible for generating, formatting, and routing its own logs.

* **Standard Library:** All logging must be implemented using Python's built-in `logging` module. No external heavy logging frameworks are required.
* **Service Identity:** Because multiple services run simultaneously, tracing an error back to its source can be difficult. Therefore, each service must instantiate its logger with an explicit name that prepends every log message.
  * *Example Format:* `[VehicleService] 2026-06-08 14:00:00 - INFO - Connected to Database.`
  * *Example Format:* `[RentalService] 2026-06-08 14:05:00 - ERROR - Failed to contact Vehicle Service.`

---

## 3. The Dual-Handler Strategy

To fulfill both operational needs (Docker aggregation) and strict exercise requirements (physical files), every logger must be configured with exactly two handlers:

1. **StreamHandler (`stdout`):** 
   * **Why:** Containerized applications should write logs to `stdout`/`stderr`. This allows Docker (and orchestration tools like `docker-compose`) to capture the output natively.
   * **Benefit:** You can view the live, aggregated logs of *all* services simultaneously by simply running `docker-compose logs -f` in your terminal.

2. **FileHandler (`app.log`):** 
   * **Why:** The project specifically mandates physical log file persistence at the service level.
   * **Implementation:** The service must write to a physical file named `app.log` located within its container or mounted volume. 
   * **Benefit:** Provides a persistent, queryable record of the service's history that survives container restarts, completely independent of the Docker daemon's internal log rotation.
