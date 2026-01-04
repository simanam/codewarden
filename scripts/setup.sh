#!/bin/bash
set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           CODEWARDEN DEVELOPMENT SETUP                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

command -v python3.11 >/dev/null 2>&1 || { echo -e "${RED}Python 3.11 is required but not installed.${NC}" >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo -e "${RED}Node.js is required but not installed.${NC}" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required but not installed.${NC}" >&2; exit 1; }
command -v poetry >/dev/null 2>&1 || command -v ~/.local/bin/poetry >/dev/null 2>&1 || { echo -e "${RED}Poetry is required but not installed.${NC}" >&2; exit 1; }
command -v pnpm >/dev/null 2>&1 || { echo -e "${RED}pnpm is required but not installed.${NC}" >&2; exit 1; }

echo -e "${GREEN}✓ All prerequisites installed${NC}"
echo ""

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env created - please edit with your values${NC}"
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi
echo ""

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
cd packages/api
~/.local/bin/poetry install 2>/dev/null || poetry install
cd ../..

cd packages/sdk-python
~/.local/bin/poetry install 2>/dev/null || poetry install
cd ../..
echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo ""

# Install Node dependencies
echo -e "${YELLOW}Installing Node dependencies...${NC}"
pnpm install
cd packages/dashboard
pnpm install
cd ../..

cd packages/sdk-js
pnpm install
cd ../..
echo -e "${GREEN}✓ Node dependencies installed${NC}"
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    SETUP COMPLETE!                            ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║  Next steps:                                                  ║"
echo "║  1. Edit .env with your API keys                              ║"
echo "║  2. Run: ./scripts/dev.sh start                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
