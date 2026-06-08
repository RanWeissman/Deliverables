# Stage 9: Containerization of Services - Deep Dive

This document provides a detailed exploration of **Stage 9** from the `project_implementation_plan.md`. It explains the mechanics of packaging the custom Python microservices into Docker containers and orchestrating their exact startup sequence.

## Overview
In Stage 3, the foundational "backing services" (PostgreSQL, RabbitMQ, Prometheus) were established. Stage 9 completes the infrastructure picture by containerizing the four custom FastAPI applications (Gateway, Vehicle, Rental, Return) so they can run identically on any developer's machine or in production.

---

## 1. Per-Service Dockerfiles

Because the architecture utilizes a Monorepo with strictly isolated microservices (Stage 1), there is no single root `Dockerfile`. 

* **The Requirement:** A distinct `Dockerfile` must be written inside each of the four service directories (`gateway_service/Dockerfile`, `vehicle_service/Dockerfile`, etc.).
* **The `uv` Build Process:** 
  * Each `Dockerfile` should use the official Python 3.14.5 image as its base.
  * It will install `uv` globally within the container.
  * It will copy only that specific service's `pyproject.toml` to install dependencies rapidly.
  * This guarantees that the Gateway container doesn't accidentally install SQLAlchemy, maintaining a minimal image footprint.
* **Execution:** The final command (`CMD`) in the Dockerfile will use Uvicorn to serve the FastAPI application (e.g., `uvicorn main:app --host 0.0.0.0 --port 8000`).

---

## 2. Docker Compose Integration

Once the Dockerfiles are written, the custom services must be injected into the existing `docker-compose.yml`.

* **Build Contexts:** Instead of pulling pre-built images from Docker Hub, the compose file uses the `build: ./vehicle_service` directive. This tells Docker Compose to build the local source code into an image dynamically.
* **Network Injection:** The services must be explicitly attached to the `drivenow_net` internal bridge network. This allows them to securely resolve and communicate with the Postgres and RabbitMQ containers using just their container names.
* **Configuration:** The compose file maps the necessary environment variables into the containers, satisfying the strict requirements of Pydantic's `BaseSettings` defined in Stage 2 (e.g., injecting `DATABASE_URL=postgresql://user:pass@postgres:5432/vehicle_db`).

---

## 3. Strict Requirement: Boot Sequencing (`depends_on`)

In a distributed system, the order in which services turn on is critical.

* **The Problem (Race Conditions):** A custom FastAPI service might take 1 second to boot, while a heavy Java-based or Erlang-based system like RabbitMQ might take 10 seconds to fully initialize its message queues. If the Return Service tries to connect to RabbitMQ before RabbitMQ is ready, the Return Service will throw a connection error and crash.
* **The Solution:** The implementation plan strictly requires configuring `depends_on` in the `docker-compose.yml`.
* **Health Checks:** It is not enough to simply say `depends_on: rabbitmq`. You must implement Docker Healthchecks. 
  * The RabbitMQ container must have a `healthcheck` script that pings the queue engine.
  * The custom Python services must define `depends_on: rabbitmq: condition: service_healthy`. 
  * This explicitly forces Docker to hold the custom services in a "waiting" state until RabbitMQ officially reports itself as fully operational, guaranteeing a smooth, crash-free deployment when you run `docker-compose up`.
