# CodeWarden API

FastAPI backend for CodeWarden - security and observability platform.

## Development

```bash
# Install dependencies
poetry install

# Run development server
poetry run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
