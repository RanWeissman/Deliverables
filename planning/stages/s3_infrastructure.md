# Stage 3: Infrastructure Orchestration - Deep Dive

This document provides a detailed exploration of **Stage 3** from the `project_implementation_plan.md`. It explains the reasoning and architecture behind the foundational backing services defined in the `docker-compose.yml` file.

## Overview

Before the custom microservices (Gateway, Vehicle, Rental, Return) can run, the foundational infrastructure must be established. Stage 3 focuses exclusively on using Docker Compose to orchestrate these third-party "backing services." By declaring these dependencies as code, the environment becomes completely reproducible.

---

## 1. Core Backing Services

The architecture dictates the deployment of three specific infrastructure containers:

### PostgreSQL (The Database Engine)
* **Role:** Acts as the primary, robust data store for the entire system.
* **Why PostgreSQL?** The implementation plan strictly requires PostgreSQL over simpler file-based databases like SQLite. The primary reason is **Concurrency and Scalability**. 
  * PostgreSQL features advanced **row-level locking**. When multiple workers from the Vehicle or Rental services attempt to read/write concurrently, PostgreSQL prevents file-locking bottlenecks.
  * This allows the microservices to scale horizontally (adding more instances or workers) without database contention.
* **Microservice Data Isolation:** Even though a single PostgreSQL container is spun up, the physical or logical separation of data must be maintained. The Vehicle Service and Rental Service will connect to entirely separate logical databases or isolated schemas within this PostgreSQL instance to enforce strict domain boundaries.

### RabbitMQ (The Message Broker)
* **Role:** The backbone of **Asynchronous (Event-Driven) Communication**.
* **Why RabbitMQ?** When the Return Service accepts a car return, it shouldn't block the client while waiting for the Rental and Vehicle services to update their databases. Instead, it instantly publishes a `ReturnRequestedEvent` to RabbitMQ.
* **Mechanism:** RabbitMQ holds these messages in a queue and guarantees delivery to consumers. This decouples the services, ensuring high availability even if a downstream service is temporarily slow or offline.

### Prometheus (The Metrics Engine)
* **Role:** The centralized observability tool used to monitor system health and performance.
* **Mechanism:** Unlike RabbitMQ (which pushes/pulls events asynchronously), Prometheus uses a **Synchronous** polling model. It periodically "scrapes" `/metrics` endpoints exposed by the four FastAPI microservices.
* **Metrics Tracked:** It will collect data such as the average response times on the Gateway and the number of HTTP requests processed, allowing the generation of real-time monitoring dashboards.

---

## 2. Internal Docker Networking (`drivenow_net`)

Containers must be able to communicate with one another securely.

* **The Bridge Network:** The `docker-compose.yml` must define a custom internal bridge network (e.g., `drivenow_net`). 
* **Internal DNS Resolution:** Placing all backing services (and eventually the custom APIs) on this network allows Docker to resolve container names to internal IP addresses automatically. 
  * *Example:* A microservice can connect to the database using the URL `postgresql://user:pass@postgres:5432/db` where `postgres` is simply the name of the container, rather than a hardcoded IP address.

---

## 3. Data Persistence via Docker Volumes

Containers are ephemeral by design; if a container is destroyed, all data inside it is lost. 

* **The Requirement:** To prevent the loss of rental records, fleet data, and unacknowledged messages upon a restart, the `docker-compose.yml` must utilize Docker Volumes.
* **Implementation:** Volumes map a secure location on the host machine to directories inside the container. 
  * For PostgreSQL, the `/var/lib/postgresql/data` path must be mapped to a volume.
  * For RabbitMQ, its persistent message store must also be backed by a volume.
  * This ensures that stopping or recreating the infrastructure does not wipe the system's memory.
