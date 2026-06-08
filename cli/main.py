import click
import httpx
from rich.console import Console
from rich.table import Table
from rich import print_json

console = Console()
GATEWAY_URL = "http://127.0.0.1:8000"

@click.group()
def cli():
    """DriveNow API CLI"""
    pass

from small_example import run_example
cli.add_command(run_example, name="demo")

@cli.group()
def cars():
    """Manage cars in the fleet"""
    pass

@cars.command("add")
@click.option("--model", required=True, help="Car model")
@click.option("--year", required=True, type=int, help="Car year")
@click.option("--status", default="Available", help="Car status")
def add_car(model, year, status):
    """Add a new car to the fleet"""
    with httpx.Client(base_url=GATEWAY_URL) as client:
        payload = {"model": model, "year": year, "status": status}
        try:
            response = client.post("/cars", json=payload)
            response.raise_for_status()
            console.print("[green]Successfully added car![/green]")
            print_json(data=response.json())
        except httpx.HTTPError as e:
            console.print(f"[red]Error adding car:[/red] {e}")
            if hasattr(e, 'response') and e.response:
                console.print(e.response.text)

@cars.command("list")
@click.option("--status", default=None, help="Filter by status")
def list_cars(status):
    """List all cars"""
    with httpx.Client(base_url=GATEWAY_URL) as client:
        params = {"status": status} if status else {}
        try:
            response = client.get("/cars", params=params)
            response.raise_for_status()
            cars_list = response.json()
            table = Table(title="DriveNow Fleet")
            table.add_column("ID", justify="right", style="cyan")
            table.add_column("Model", style="magenta")
            table.add_column("Year", justify="right")
            table.add_column("Status", style="green")
            
            for car in cars_list:
                table.add_row(str(car["id"]), car["model"], str(car["year"]), car["status"])
            
            console.print(table)
        except httpx.HTTPError as e:
            console.print(f"[red]Error fetching cars:[/red] {e}")
            if hasattr(e, 'response') and e.response:
                console.print(e.response.text)

@cars.command("update-status")
@click.argument("car_id", type=int)
@click.option("--status", required=True, help="New status")
def update_status(car_id, status):
    """Update car status"""
    with httpx.Client(base_url=GATEWAY_URL) as client:
        payload = {"status": status}
        try:
            response = client.put(f"/cars/{car_id}/status", json=payload)
            response.raise_for_status()
            console.print("[green]Successfully updated car status![/green]")
            print_json(data=response.json())
        except httpx.HTTPError as e:
            console.print(f"[red]Error updating status:[/red] {e}")
            if hasattr(e, 'response') and e.response:
                console.print(e.response.text)

@cli.group()
def rentals():
    """Manage rentals"""
    pass

@rentals.command("create")
@click.option("--car-id", required=True, type=int)
@click.option("--customer-id", required=True, type=int)
@click.option("--customer-name", required=True, help="Customer Name")
@click.option("--start", required=True, help="Start date (YYYY-MM-DD)")
@click.option("--end", required=True, help="End date (YYYY-MM-DD)")
def create_rental(car_id, customer_id, customer_name, start, end):
    """Create a new rental"""
    with httpx.Client(base_url=GATEWAY_URL) as client:
        payload = {
            "car_id": car_id,
            "customer_id": customer_id,
            "customer_name": customer_name,
            "start_date": f"{start}T00:00:00Z",
            "end_date": f"{end}T00:00:00Z"
        }
        try:
            response = client.post("/rentals", json=payload)
            response.raise_for_status()
            console.print("[green]Successfully created rental![/green]")
            print_json(data=response.json())
        except httpx.HTTPError as e:
            console.print(f"[red]Error creating rental:[/red] {e}")
            if hasattr(e, 'response') and e.response:
                console.print(e.response.text)

@cli.group()
def returns():
    """Manage returns"""
    pass

@returns.command("process")
@click.option("--rental-id", required=True, type=int)
@click.option("--car-id", required=True, type=int)
def process_return(rental_id, car_id):
    """Process a car return"""
    with httpx.Client(base_url=GATEWAY_URL) as client:
        payload = {"rental_id": rental_id, "car_id": car_id}
        try:
            response = client.post("/returns", json=payload)
            response.raise_for_status()
            console.print("[green]Return accepted for processing![/green]")
            print_json(data=response.json())
        except httpx.HTTPError as e:
            console.print(f"[red]Error processing return:[/red] {e}")
            if hasattr(e, 'response') and e.response:
                console.print(e.response.text)

if __name__ == '__main__':
    cli()
