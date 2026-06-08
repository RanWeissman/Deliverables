# DriveNow CLI

A command-line interface for the DriveNow API Gateway, built with `Click`, `httpx`, and `Rich`.

## Requirements
* Python 3.11+
* `uv` (Fast Python package installer and resolver)
* The DriveNow Docker cluster must be running locally on port 8000.

## Installation

You don't need to manually install dependencies or create virtual environments. `uv` will handle it all on the fly!

## Usage Examples

Execute these commands directly from the **root DriveNow directory** (`C:\Users\Ran\Desktop\Ran\Projects\DriveNow`):

### 1. Add a New Car
Adds a vehicle to the fleet:
```bash
uv run --project cli cli/main.py cars add --model Mustang --year 2025
```

### 2. List All Cars
Displays a beautifully formatted table of all vehicles in the fleet:
```bash
uv run --project cli cli/main.py cars list
```

**List Cars by Status:**
Filter the fleet to only see cars with a specific status (e.g., "In use", "Maintenance"):
```bash
uv run --project cli cli/main.py cars list --status "In use"
```

### 3. Update Car Status
Manually update a car's status (e.g., from Available to Maintenance):
```bash
uv run --project cli cli/main.py cars update-status 1 --status "Maintenance"
```

### 4. Create a Rental
Rents out a vehicle, instantly updating the vehicle's status to "In use":
```bash
uv run --project cli cli/main.py rentals create --car-id 1 --customer-id 101 --customer-name "John Doe" --start 2026-06-08 --end 2026-06-10
```

### 5. Return a Car
Processes a vehicle return, asynchronously freeing up the vehicle:
```bash
uv run --project cli cli/main.py returns process --rental-id 1 --car-id 1
```
