# Utils Package Implementation Plan

## Goal Description

Create a new directory called `utils` to act as a shared package for all the existing microservices (`gateway_service`, `rental_service`, `return_service`, `vehicle_service`, etc.). Currently, common modules like `logger.py`, `config.py`, `schemas.py`, and database components (`db`) are duplicated across these services. The goal of this change is to extract these common components into the `utils` package to avoid code replication, simplify maintenance, and ensure consistency across the entire project.

> [!NOTE]
> This will involve making `utils` an installable Python package (e.g., using a `pyproject.toml` file) so that the microservices can declare it as a local dependency.

## User Review Required

> [!IMPORTANT]  
> **Directory Placement:** Should `utils` be placed in the project root (`/utils`) or inside the `src` directory (`/src/utils`)? This plan assumes `/src/utils` to keep all code contained inside `src`.
> 
> **Docker Builds:** Moving shared code outside of the individual service directories means we will need to update the `Dockerfile` for each service. The Docker build context will likely need to be elevated to the project root or `src` directory so that both the service code and the `utils` code can be copied into the container.

## Proposed Changes

### 1. Create the `utils` Package

Create a new directory `src/utils` structured as a Python package.

#### [NEW] [src/utils/pyproject.toml](file:///c:/Users/Ran/Desktop/Ran/Projects/DriveNow/src/utils/pyproject.toml)
Define the `utils` package and its third-party dependencies (like `pydantic`, `sqlalchemy`, `logging` extensions, etc.).

#### [NEW] [src/utils/src/__init__.py](file:///c:/Users/Ran/Desktop/Ran/Projects/DriveNow/src/utils/src/__init__.py)
Initialize the package.

### 2. Extract Shared Components

Consolidate the duplicated code into the new package.

#### [NEW] [src/utils/src/logger.py](file:///c:/Users/Ran/Desktop/Ran/Projects/DriveNow/src/utils/src/logger.py)
Move the standard logging configuration here. The `get_logger` function (or equivalent) will be updated to accept a `service_name` parameter so that each service can inject its own name. This ensures that all logs have a consistent format and can be easily identified by their origin service.

#### [NEW] [src/utils/src/config.py](file:///c:/Users/Ran/Desktop/Ran/Projects/DriveNow/src/utils/src/config.py)
Create a base `Settings` class that encapsulates standard configuration. Individual services can inherit from this base class to add their own service-specific environment variables and overrides.

#### [NEW] [src/utils/src/db/](file:///c:/Users/Ran/Desktop/Ran/Projects/DriveNow/src/utils/src/db/)
Move the core database connection logic (like `get_db()`), session factory setup, and the declarative `Base` here. The connection string itself will be injected by the service's own configuration, and service-specific database models will remain in the individual service directories.

#### [NEW] [src/utils/src/schemas.py](file:///c:/Users/Ran/Desktop/Ran/Projects/DriveNow/src/utils/src/schemas.py)
Extract common Pydantic schemas (e.g., standard responses, base models). Service-specific schemas will remain in their respective service directories, inheriting from these common base schemas where appropriate.

### 3. Update Existing Services

For each service (`gateway_service`, `rental_service`, `return_service`, `vehicle_service`):

#### [MODIFY] pyproject.toml
Add `utils` as a local dependency (e.g., `utils = { path = "../../utils", develop = true }`).

#### [DELETE] Service-specific duplicates
Remove local `logger.py`, duplicated `schemas.py`, and duplicate `db/` connection codes.

#### [MODIFY] Service Source Code (*.py)
Keep service-specific overrides in the services while using `utils` for the base implementations:
- **Config:** Create service-specific settings inheriting from the base: `class RentalSettings(BaseSettings): ...`
- **Database:** Keep local models and import the session factory/Base from `utils.db`.
- **Schemas:** Define service-specific request/response schemas extending `utils.schemas.BaseResponse` (or similar).

Update import statements across the services:
```diff
- from src.logger import get_logger
+ from utils.logger import get_logger
```
Update `get_logger` calls to pass the service's name:
```diff
- logger = get_logger(__name__)
+ logger = get_logger("gateway_service") # example for gateway_service
```

### 4. Update Dockerfiles

#### [MODIFY] Service Dockerfiles
Adjust the Dockerfiles to copy the `utils` directory during the build process, and adjust the `uv` installation step to account for the local package dependency.

## Verification Plan

### Automated Tests
- Run `pytest` inside each service directory to ensure tests still pass after refactoring imports.
- Validate that the `utils` package itself can run its own independent tests (if added).

### Manual Verification
- Rebuild all Docker containers using `docker-compose build`.
- Bring up the system using `docker-compose up` and verify that the Gateway can still route requests to the Rental and Return services.
- Check service logs to confirm that the centralized `logger` from `utils` is formatting messages correctly.
