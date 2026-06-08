# Stage 1: Monorepo Structure & Dependency Management - Deep Dive

This document provides an in-depth explanation of **Stage 1** from the `project_implementation_plan.md`, focusing on establishing the structural foundation, managing isolated dependencies, and understanding the core technology stack for the DriveNow microservices architecture.

## 1. Architectural Choice: Monorepo with Isolated Microservices

The system employs a "Monorepo" structure (a single Git repository) containing distinct, isolated microservices. While it's one repository, it acts structurally like a polyrepo by enforcing strict boundaries.

* **Distinct Directories:** The project is divided into four completely separate service directories: `gateway_service`, `vehicle_service`, `rental_service`, and `return_service`.
* **Zero Shared Code by Default:** To enforce strict microservice boundaries, the services do not share a common generic library at the top level. Each service is treated as an independent application.
* **Version Control:** A single `.git` initialization at the root level simplifies version control for the entire exercise while the isolated folders maintain service autonomy.
* **`.gitignore`:** A comprehensive root `.gitignore` is critical to prevent committing virtual environments (`.venv`), Python cache files (`__pycache__`), environment variables (`.env`), and IDE-specific configurations.

## 2. Python Version & `uv` for Dependency Management

* **Python 3.14.5+:** The project explicitly mandates Python 3.14.5 or higher to ensure all developers and production containers are using compatible interpreter capabilities and standard library features.
* **The Switch to `uv`:** The architecture mandates the use of **uv** (replacing standard tools like pip/venv). `uv` is an extremely fast, Rust-based Python package and project manager. 
* **Per-Service Environments:** Crucially, there is no root-level `pyproject.toml` or `requirements.txt`. Instead, you must run `uv init` *inside* each service folder.
  * This guarantees that the `gateway_service` has its own `pyproject.toml` and `.venv`, entirely separate from the `vehicle_service`.
  * This isolation prevents dependency hell (e.g., if one service needs an older version of Pydantic while another needs the latest).

## 3. Core Dependencies Breakdown

Every service must include the following foundational packages in its respective `pyproject.toml`, serving specific architectural roles:

### Web Framework & Server
* **`fastapi`**: The core framework used to build the RESTful APIs. It was chosen for its high performance, native async support, and automatic OpenAPI documentation generation.
* **`uvicorn`**: The ASGI (Asynchronous Server Gateway Interface) web server used to run the FastAPI applications concurrently.

### Database Layer (Vehicle & Rental Services)
* **`sqlalchemy`**: The chosen Object Relational Mapper (ORM) for interacting with the PostgreSQL database. It allows developers to define Python classes (`cars`, `rentals`) that map to database tables, handling connections, transactions, and session management.

### Validation & Configuration
* **`pydantic`**: Used heavily by FastAPI for validating incoming HTTP request bodies and serializing outgoing responses.
* **`pydantic-settings`**: Critical for Stage 2. It parses environment variables (like Database URLs or RabbitMQ credentials) and validates them at startup, ensuring the service refuses to boot if misconfigured.

### Inter-Service Communication
* **`httpx`**: A modern HTTP client used for **Synchronous** inter-service communication.
  * *Example Usage:* The Gateway uses it to proxy requests to downstream services. The Rental service uses it to verify car availability with the Vehicle service.
* **`pika` / `aio-pika`**: The clients used to connect to RabbitMQ for **Asynchronous** event-driven messaging.
  * *Example Usage:* The Return service uses this to publish `ReturnRequestedEvent` messages to a message queue.

### Quality Assurance
* **`pytest`**: The framework used to write and execute the mandatory unit tests across the services.

## 4. Initialization Checklist

To fulfill Stage 1, the following concrete tasks must be executed from the command line:

1. **Git Init:** Run `git init` in the root folder (`DriveNow/`).
2. **Scaffold Folders:** Run `mkdir gateway_service vehicle_service rental_service return_service`.
3. **Setup `.gitignore`:** Create a robust `.gitignore` for Python projects.
4. **Initialize `uv`:** `cd` into each of the four directories and run `uv init`. This creates a basic Python structure and a `pyproject.toml` for each.
5. **Add Dependencies:** Within each folder, use `uv add fastapi uvicorn sqlalchemy pydantic pydantic-settings httpx pika pytest` to populate the localized environments.
