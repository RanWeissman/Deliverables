FROM python:3.11-slim

# Copy the uv binary from the official uv image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv sync (frozen ensures exact versions are used)
RUN uv sync --frozen --no-cache

# Copy the rest of the application
COPY . .

# Expose the internal port
EXPOSE 8000

# Run the FastAPI server
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
