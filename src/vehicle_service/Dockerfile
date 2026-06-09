FROM python:3.11-slim

# Copy the uv binary from the official uv image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the shared utils package
WORKDIR /app/utils
COPY utils/ .

# Set the working directory for the service
WORKDIR /app/service

# Copy dependency definition files
COPY vehicle_service/pyproject.toml vehicle_service/uv.lock ./

# Install dependencies using uv sync (frozen ensures exact versions are used)
RUN uv sync --frozen

# Copy the rest of the application
COPY vehicle_service/ .

# Expose the internal port
EXPOSE 8000

# Run the FastAPI server
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
