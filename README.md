# CodeWarden

> You ship the code. We stand guard.

CodeWarden is a drop-in security and monitoring platform for solopreneurs.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/codewarden/codewarden.git
cd codewarden

# Setup development environment
./scripts/setup.sh

# Start all services
./scripts/dev.sh start
```

## Architecture

```
packages/
├── api/          # FastAPI backend
├── dashboard/    # Next.js frontend
├── sdk-python/   # Python SDK (codewarden)
└── sdk-js/       # JavaScript SDK (codewarden-js)
```

## Documentation

- [Getting Started](docs/getting-started/)
- [API Reference](docs/api-reference/)
- [SDK Documentation](docs/sdk/)

## License

MIT
