# CodeWarden API Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true \
    && poetry install --no-root --no-interaction

# Copy application code
COPY . .

# Install the package
RUN poetry install --no-interaction

# Expose port (Railway will use $PORT)
EXPOSE 8000

# Run the application (use shell form to expand $PORT, default to 8000)
CMD poetry run uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
