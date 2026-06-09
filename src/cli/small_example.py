import click
import httpx
import time
from rich.console import Console
from rich.table import Table

console = Console()
GATEWAY_URL = "http://127.0.0.1:8000"

def print_cars_table(cars_list, title):
    table = Table(title=title)
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Model", style="magenta")
    table.add_column("Year", justify="right")
    table.add_column("Status", style="green")
    
    for car in cars_list:
        table.add_row(str(car["id"]), car["model"], str(car["year"]), car["status"])
    
    console.print(table)

@click.command()
def run_example():
    """Runs a full end-to-end demo of the DriveNow Gateway."""
    console.print("[bold cyan]Starting DriveNow End-to-End Demo...[/bold cyan]\n")
    
    with httpx.Client(base_url=GATEWAY_URL) as client:
        # 1. Add 5 Vehicles
        console.print("[bold yellow]--- 1. Adding 5 Vehicles ---[/bold yellow]")
        vehicles = [
            {"model": "Tesla Model 3", "year": 2024, "status": "Available"},
            {"model": "Honda Civic", "year": 2022, "status": "Available"},
            {"model": "Ford F-150", "year": 2023, "status": "Available"},
            {"model": "Toyota Camry", "year": 2025, "status": "Available"},
            {"model": "BMW X5", "year": 2024, "status": "Available"},
        ]
        
        car_ids = []
        for v in vehicles:
            try:
                resp = client.post("/cars", json=v)
                resp.raise_for_status()
                car_data = resp.json()
                car_ids.append(car_data["id"])
                console.print(f"[green]Added:[/green] {v['model']} (ID: {car_data['id']})")
            except httpx.HTTPError as e:
                console.print(f"[red]Failed to add {v['model']}: {e}[/red]")
        
        time.sleep(0.5)
        
        # 2. List all cars
        console.print("\n[bold yellow]--- 2. Listing All Cars ---[/bold yellow]")
        try:
            resp = client.get("/cars")
            resp.raise_for_status()
            print_cars_table(resp.json(), "All Fleet Vehicles")
        except httpx.HTTPError as e:
            console.print(f"[red]Failed to list cars: {e}[/red]")

        # 3. Rent a car
        if car_ids:
            target_car_id = car_ids[0]
            console.print(f"\n[bold yellow]--- 3. Renting Car ID {target_car_id} ---[/bold yellow]")
            rental_payload = {
                "car_id": target_car_id,
                "customer_id": 999,
                "customer_name": "John Doe",
                "start_date": "2026-06-01T10:00:00Z",
                "end_date": "2026-06-15T10:00:00Z"
            }
            try:
                resp = client.post("/rentals", json=rental_payload)
                resp.raise_for_status()
                rental_data = resp.json()
                rental_id = rental_data["id"]
                console.print(f"[green]Rental created successfully! Rental ID: {rental_id}[/green]")
            except httpx.HTTPError as e:
                console.print(f"[red]Failed to create rental: {e}[/red]")
                rental_id = None
            
            time.sleep(0.5)

            # 4. List cars filtered by 'In use'
            console.print("\n[bold yellow]--- 4. Listing Cars 'In use' ---[/bold yellow]")
            try:
                resp = client.get("/cars", params={"status": "In use"})
                resp.raise_for_status()
                print_cars_table(resp.json(), "Rented Vehicles")
            except httpx.HTTPError as e:
                console.print(f"[red]Failed to list rented cars: {e}[/red]")

            # 5. Return the car
            if rental_id:
                console.print(f"\n[bold yellow]--- 5. Returning Car ID {target_car_id} ---[/bold yellow]")
                return_payload = {
                    "rental_id": rental_id,
                    "car_id": target_car_id
                }
                try:
                    resp = client.post("/returns", json=return_payload)
                    resp.raise_for_status()
                    console.print(f"[green]Return processed successfully![/green]")
                except httpx.HTTPError as e:
                    console.print(f"[red]Failed to process return: {e}[/red]")
                
                time.sleep(0.5)

                # 6. List all cars to verify availability
                console.print("\n[bold yellow]--- 6. Listing All Cars (Verify Return) ---[/bold yellow]")
                try:
                    resp = client.get("/cars")
                    resp.raise_for_status()
                    print_cars_table(resp.json(), "Fleet After Return")
                except httpx.HTTPError as e:
                    console.print(f"[red]Failed to verify final fleet state: {e}[/red]")

    console.print("\n[bold cyan]Demo completed successfully![/bold cyan]")

if __name__ == "__main__":
    run_example()
