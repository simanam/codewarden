#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

case "$1" in
    setup)
        ./scripts/setup.sh
        ;;

    start)
        print_header "Starting CodeWarden Development Environment"

        echo -e "${YELLOW}Starting Docker services...${NC}"
        docker-compose up -d

        echo ""
        echo -e "${GREEN}✓ All services started!${NC}"
        echo ""
        echo "┌─────────────────────────────────────────────────────────────┐"
        echo "│  Service            │  URL                                 │"
        echo "├─────────────────────┼──────────────────────────────────────┤"
        echo "│  Dashboard          │  http://localhost:3000               │"
        echo "│  API                │  http://localhost:8000               │"
        echo "│  API Docs           │  http://localhost:8000/docs          │"
        echo "│  OpenObserve        │  http://localhost:5080               │"
        echo "│  Redis              │  localhost:6379                      │"
        echo "└─────────────────────┴──────────────────────────────────────┘"
        ;;

    stop)
        print_header "Stopping CodeWarden"
        docker-compose down
        echo -e "${GREEN}✓ All services stopped${NC}"
        ;;

    restart)
        print_header "Restarting CodeWarden"
        docker-compose restart
        echo -e "${GREEN}✓ All services restarted${NC}"
        ;;

    logs)
        SERVICE=${2:-api}
        print_header "Logs for: $SERVICE"
        docker-compose logs -f $SERVICE
        ;;

    status)
        print_header "Service Status"
        docker-compose ps
        ;;

    test)
        print_header "Running All Tests"

        echo -e "${YELLOW}Testing API...${NC}"
        cd packages/api && (~/.local/bin/poetry run pytest -v || poetry run pytest -v) && cd ../..

        echo -e "${YELLOW}Testing Python SDK...${NC}"
        cd packages/sdk-python && (~/.local/bin/poetry run pytest -v || poetry run pytest -v) && cd ../..

        echo -e "${YELLOW}Testing JavaScript SDK...${NC}"
        cd packages/sdk-js && pnpm test && cd ../..

        echo -e "${GREEN}✓ All tests passed!${NC}"
        ;;

    lint)
        print_header "Running Linters"

        echo -e "${YELLOW}Linting Python...${NC}"
        cd packages/api && (~/.local/bin/poetry run ruff check . || poetry run ruff check .) && cd ../..
        cd packages/sdk-python && (~/.local/bin/poetry run ruff check . || poetry run ruff check .) && cd ../..

        echo -e "${YELLOW}Linting TypeScript...${NC}"
        cd packages/sdk-js && pnpm lint && cd ../..
        cd packages/dashboard && pnpm lint && cd ../..

        echo -e "${GREEN}✓ Linting complete${NC}"
        ;;

    clean)
        print_header "Cleaning Up"
        docker-compose down -v --remove-orphans 2>/dev/null || true
        rm -rf packages/api/.venv
        rm -rf packages/sdk-python/.venv
        rm -rf packages/dashboard/node_modules
        rm -rf packages/sdk-js/node_modules
        rm -rf packages/dashboard/.next
        rm -rf node_modules
        echo -e "${GREEN}✓ Cleanup complete${NC}"
        ;;

    *)
        echo "CodeWarden Development CLI"
        echo ""
        echo "Usage: ./scripts/dev.sh <command>"
        echo ""
        echo "Commands:"
        echo "  setup       First-time setup"
        echo "  start       Start all services"
        echo "  stop        Stop all services"
        echo "  restart     Restart all services"
        echo "  logs [svc]  View logs (default: api)"
        echo "  status      Show service status"
        echo "  test        Run all tests"
        echo "  lint        Run linters"
        echo "  clean       Remove all containers and dependencies"
        ;;
esac
