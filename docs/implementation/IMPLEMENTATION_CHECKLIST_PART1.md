# CodeWarden Implementation Checklist
## Part 1: Foundation & Infrastructure Setup

**Document Version:** 1.0  
**Status:** Ready for Implementation  
**Last Updated:** January 2026  
**Estimated Duration:** Weeks 1-2

---

## Document Navigation

| Part | Focus Area | Status |
|------|------------|--------|
| **Part 1** | Foundation & Infrastructure Setup | 📍 Current |
| Part 2 | Core Product Development (SDK + API) | Next |
| Part 3 | Frontend, Integration & Launch | Final |

---

## Overview

This document covers:
- Development environment setup
- Monorepo initialization
- Database and infrastructure provisioning
- CI/CD pipeline configuration
- Local development tooling

---

# Phase 1: Development Environment Setup

## Story 1.1: Local Machine Preparation

### Task 1.1.1: Install Required Tools

**Sub-tasks:**

- [ ] **1.1.1.1** Install Python 3.11+
  ```bash
  # macOS
  brew install python@3.11
  
  # Ubuntu
  sudo apt update
  sudo apt install python3.11 python3.11-venv python3.11-dev
  
  # Verify
  python3.11 --version
  ```

- [ ] **1.1.1.2** Install Node.js 20 LTS
  ```bash
  # Using nvm (recommended)
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
  nvm install 20
  nvm use 20
  
  # Verify
  node --version  # Should be v20.x.x
  npm --version
  ```

- [ ] **1.1.1.3** Install Docker Desktop
  ```bash
  # macOS
  brew install --cask docker
  
  # Ubuntu
  sudo apt install docker.io docker-compose-v2
  sudo usermod -aG docker $USER
  
  # Verify
  docker --version
  docker-compose --version
  ```

- [ ] **1.1.1.4** Install Git and configure
  ```bash
  # Install
  brew install git  # macOS
  sudo apt install git  # Ubuntu
  
  # Configure
  git config --global user.name "Your Name"
  git config --global user.email "your@email.com"
  git config --global init.defaultBranch main
  ```

- [ ] **1.1.1.5** Install Poetry (Python package manager)
  ```bash
  curl -sSL https://install.python-poetry.org | python3 -
  
  # Add to PATH (add to ~/.bashrc or ~/.zshrc)
  export PATH="$HOME/.local/bin:$PATH"
  
  # Verify
  poetry --version
  ```

- [ ] **1.1.1.6** Install pnpm (Node package manager)
  ```bash
  npm install -g pnpm
  
  # Verify
  pnpm --version
  ```

- [ ] **1.1.1.7** Install IDE extensions
  ```
  VS Code Extensions:
  - [ ] Python (ms-python.python)
  - [ ] Pylance (ms-python.vscode-pylance)
  - [ ] ESLint (dbaeumer.vscode-eslint)
  - [ ] Prettier (esbenp.prettier-vscode)
  - [ ] Tailwind CSS IntelliSense (bradlc.vscode-tailwindcss)
  - [ ] Docker (ms-azuretools.vscode-docker)
  - [ ] GitLens (eamodio.gitlens)
  ```

**Testing:**
- [ ] Run `python3.11 --version` → Outputs `Python 3.11.x`
- [ ] Run `node --version` → Outputs `v20.x.x`
- [ ] Run `docker run hello-world` → Outputs success message
- [ ] Run `poetry --version` → Outputs version
- [ ] Run `pnpm --version` → Outputs version

---

### Task 1.1.2: Install CLI Tools

**Sub-tasks:**

- [ ] **1.1.2.1** Install Railway CLI
  ```bash
  # macOS
  brew install railway
  
  # Other platforms
  npm install -g @railway/cli
  
  # Login
  railway login
  ```

- [ ] **1.1.2.2** Install Vercel CLI
  ```bash
  npm install -g vercel
  
  # Login
  vercel login
  ```

- [ ] **1.1.2.3** Install Supabase CLI
  ```bash
  # macOS
  brew install supabase/tap/supabase
  
  # npm (alternative)
  npm install -g supabase
  
  # Login
  supabase login
  ```

- [ ] **1.1.2.4** Install Redis CLI tools
  ```bash
  # macOS
  brew install redis
  
  # Ubuntu
  sudo apt install redis-tools
  ```

- [ ] **1.1.2.5** Install HTTPie (API testing)
  ```bash
  # macOS
  brew install httpie
  
  # pip
  pip install httpie
  ```

**Testing:**
- [ ] Run `railway --version` → Outputs version
- [ ] Run `vercel --version` → Outputs version
- [ ] Run `supabase --version` → Outputs version
- [ ] Run `http --version` → Outputs version

---

## Story 1.2: Monorepo Initialization

### Task 1.2.1: Create Repository Structure

**Sub-tasks:**

- [ ] **1.2.1.1** Create GitHub repository
  ```bash
  # Create on GitHub: github.com/new
  # Repository name: codewarden
  # Visibility: Private (initially)
  # Initialize with README: No
  # Add .gitignore: None (we'll create custom)
  # License: MIT
  ```

- [ ] **1.2.1.2** Clone and initialize local repo
  ```bash
  git clone https://github.com/YOUR_USERNAME/codewarden.git
  cd codewarden
  ```

- [ ] **1.2.1.3** Create root directory structure
  ```bash
  mkdir -p packages/{api,dashboard,sdk-python,sdk-js}
  mkdir -p docs/{getting-started,features,sdk,api-reference}
  mkdir -p infrastructure/{terraform,scripts}
  mkdir -p scripts
  mkdir -p .github/workflows
  ```

- [ ] **1.2.1.4** Create root `.gitignore`
  ```bash
  cat > .gitignore << 'EOF'
  # Dependencies
  node_modules/
  __pycache__/
  *.pyc
  .venv/
  venv/
  .env
  .env.local
  .env.*.local
  
  # Build outputs
  dist/
  build/
  *.egg-info/
  .next/
  out/
  
  # IDE
  .idea/
  .vscode/
  *.swp
  *.swo
  
  # OS
  .DS_Store
  Thumbs.db
  
  # Testing
  .coverage
  htmlcov/
  .pytest_cache/
  coverage/
  
  # Logs
  *.log
  logs/
  
  # Docker
  .docker/
  
  # Secrets (NEVER commit)
  *.pem
  *.key
  secrets/
  EOF
  ```

- [ ] **1.2.1.5** Create root `README.md`
  ```bash
  cat > README.md << 'EOF'
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
  EOF
  ```

- [ ] **1.2.1.6** Create `LICENSE` file
  ```bash
  cat > LICENSE << 'EOF'
  MIT License
  
  Copyright (c) 2026 CodeWarden
  
  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:
  
  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.
  
  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.
  EOF
  ```

**Testing:**
- [ ] Run `ls -la` → Shows all created directories
- [ ] Run `cat .gitignore` → Shows ignore patterns
- [ ] Run `cat README.md` → Shows formatted README

---

### Task 1.2.2: Create Environment Configuration

**Sub-tasks:**

- [ ] **1.2.2.1** Create `.env.example` template
  ```bash
  cat > .env.example << 'EOF'
  # ═══════════════════════════════════════════════════════════════
  # CODEWARDEN ENVIRONMENT CONFIGURATION
  # ═══════════════════════════════════════════════════════════════
  # Copy this file to .env and fill in the values
  # NEVER commit .env to version control
  
  # ───────────────────────────────────────────────────────────────
  # ENVIRONMENT
  # ───────────────────────────────────────────────────────────────
  ENVIRONMENT=development
  LOG_LEVEL=debug
  
  # ───────────────────────────────────────────────────────────────
  # DATABASE (Supabase)
  # ───────────────────────────────────────────────────────────────
  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
  SUPABASE_URL=http://localhost:8000

  # NEW API Keys (2025+) - Use these for new projects
  # Get from: Supabase Dashboard → Project Settings → API
  SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx
  SUPABASE_SECRET_KEY=sb_secret_xxx

  # LEGACY API Keys (deprecated, will be removed)
  # Only use if your project was created before Nov 2025
  # SUPABASE_ANON_KEY=your-anon-key
  # SUPABASE_SERVICE_KEY=your-service-key
  
  # ───────────────────────────────────────────────────────────────
  # REDIS (Local/Upstash)
  # ───────────────────────────────────────────────────────────────
  REDIS_URL=redis://localhost:6379
  # For Upstash (production):
  # UPSTASH_REDIS_REST_URL=https://xxx.upstash.io
  # UPSTASH_REDIS_REST_TOKEN=xxx
  
  # ───────────────────────────────────────────────────────────────
  # OPENOBSERVE (Log Storage)
  # ───────────────────────────────────────────────────────────────
  OPENOBSERVE_URL=http://localhost:5080
  OPENOBSERVE_ORG=default
  OPENOBSERVE_USER=admin@codewarden.local
  OPENOBSERVE_PASSWORD=admin123
  
  # ───────────────────────────────────────────────────────────────
  # AI PROVIDERS
  # ───────────────────────────────────────────────────────────────
  # Get keys from:
  # - Google: https://makersuite.google.com/app/apikey
  # - Anthropic: https://console.anthropic.com/
  # - OpenAI: https://platform.openai.com/api-keys
  GOOGLE_API_KEY=
  ANTHROPIC_API_KEY=
  OPENAI_API_KEY=
  
  # ───────────────────────────────────────────────────────────────
  # NOTIFICATIONS
  # ───────────────────────────────────────────────────────────────
  # Resend: https://resend.com/api-keys
  RESEND_API_KEY=re_xxx
  
  # Telegram: https://t.me/BotFather
  TELEGRAM_BOT_TOKEN=
  
  # ───────────────────────────────────────────────────────────────
  # STORAGE (Cloudflare R2)
  # ───────────────────────────────────────────────────────────────
  CLOUDFLARE_R2_ACCESS_KEY_ID=
  CLOUDFLARE_R2_SECRET_ACCESS_KEY=
  CLOUDFLARE_R2_BUCKET=codewarden-evidence
  CLOUDFLARE_R2_ENDPOINT=
  
  # ───────────────────────────────────────────────────────────────
  # API CONFIGURATION
  # ───────────────────────────────────────────────────────────────
  API_HOST=0.0.0.0
  API_PORT=8000
  API_WORKERS=1
  
  # ───────────────────────────────────────────────────────────────
  # DASHBOARD CONFIGURATION
  # ───────────────────────────────────────────────────────────────
  NEXT_PUBLIC_API_URL=http://localhost:8000
  NEXT_PUBLIC_SUPABASE_URL=http://localhost:8000

  # NEW: Use publishable key (safe for browser/frontend)
  NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx

  # LEGACY (deprecated)
  # NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
  EOF
  ```

- [ ] **1.2.2.2** Create local `.env` from template
  ```bash
  cp .env.example .env
  # Edit .env with your actual values
  ```

- [ ] **1.2.2.3** Create `.env.test` for testing
  ```bash
  cat > .env.test << 'EOF'
  ENVIRONMENT=test
  LOG_LEVEL=warning
  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres_test
  REDIS_URL=redis://localhost:6379/1
  OPENOBSERVE_URL=http://localhost:5080
  GOOGLE_API_KEY=test-key
  ANTHROPIC_API_KEY=test-key
  OPENAI_API_KEY=test-key
  EOF
  ```

**Testing:**
- [ ] Run `cat .env.example` → Shows all configuration options
- [ ] Verify `.env` exists and is in `.gitignore`

---

### Task 1.2.3: Create Development Scripts

**Sub-tasks:**

- [ ] **1.2.3.1** Create `scripts/setup.sh`
  ```bash
  cat > scripts/setup.sh << 'EOF'
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
  command -v poetry >/dev/null 2>&1 || { echo -e "${RED}Poetry is required but not installed.${NC}" >&2; exit 1; }
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
  
  # Pull Docker images
  echo -e "${YELLOW}Pulling Docker images...${NC}"
  docker-compose pull
  echo -e "${GREEN}✓ Docker images pulled${NC}"
  echo ""
  
  # Start infrastructure services
  echo -e "${YELLOW}Starting infrastructure services...${NC}"
  docker-compose up -d supabase-db redis openobserve
  echo -e "${GREEN}✓ Infrastructure services started${NC}"
  echo ""
  
  # Wait for services to be ready
  echo -e "${YELLOW}Waiting for services to be ready...${NC}"
  sleep 10
  echo -e "${GREEN}✓ Services ready${NC}"
  echo ""
  
  # Install Python dependencies
  echo -e "${YELLOW}Installing Python dependencies...${NC}"
  cd packages/api
  poetry install
  cd ../..
  
  cd packages/sdk-python
  poetry install
  cd ../..
  echo -e "${GREEN}✓ Python dependencies installed${NC}"
  echo ""
  
  # Install Node dependencies
  echo -e "${YELLOW}Installing Node dependencies...${NC}"
  cd packages/dashboard
  pnpm install
  cd ../..
  
  cd packages/sdk-js
  pnpm install
  cd ../..
  echo -e "${GREEN}✓ Node dependencies installed${NC}"
  echo ""
  
  # Run database migrations
  echo -e "${YELLOW}Running database migrations...${NC}"
  cd packages/api
  poetry run alembic upgrade head
  cd ../..
  echo -e "${GREEN}✓ Database migrations complete${NC}"
  echo ""
  
  echo "╔═══════════════════════════════════════════════════════════════╗"
  echo "║                    SETUP COMPLETE! 🎉                         ║"
  echo "╠═══════════════════════════════════════════════════════════════╣"
  echo "║  Next steps:                                                  ║"
  echo "║  1. Edit .env with your API keys                              ║"
  echo "║  2. Run: ./scripts/dev.sh start                               ║"
  echo "╚═══════════════════════════════════════════════════════════════╝"
  EOF
  
  chmod +x scripts/setup.sh
  ```

- [ ] **1.2.3.2** Create `scripts/dev.sh`
  ```bash
  cat > scripts/dev.sh << 'EOF'
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
          print_header "🚀 Starting CodeWarden Development Environment"
          
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
          echo "│  Supabase Studio    │  http://localhost:3001               │"
          echo "│  OpenObserve        │  http://localhost:5080               │"
          echo "│  Redis              │  localhost:6379                      │"
          echo "└─────────────────────┴──────────────────────────────────────┘"
          ;;
          
      stop)
          print_header "🛑 Stopping CodeWarden"
          docker-compose down
          echo -e "${GREEN}✓ All services stopped${NC}"
          ;;
          
      restart)
          print_header "🔄 Restarting CodeWarden"
          docker-compose restart
          echo -e "${GREEN}✓ All services restarted${NC}"
          ;;
          
      logs)
          SERVICE=${2:-api}
          print_header "📋 Logs for: $SERVICE"
          docker-compose logs -f $SERVICE
          ;;
          
      status)
          print_header "📊 Service Status"
          docker-compose ps
          ;;
          
      test)
          print_header "🧪 Running All Tests"
          
          echo -e "${YELLOW}Testing API...${NC}"
          cd packages/api && poetry run pytest -v && cd ../..
          
          echo -e "${YELLOW}Testing Python SDK...${NC}"
          cd packages/sdk-python && poetry run pytest -v && cd ../..
          
          echo -e "${YELLOW}Testing JavaScript SDK...${NC}"
          cd packages/sdk-js && pnpm test && cd ../..
          
          echo -e "${YELLOW}Testing Dashboard...${NC}"
          cd packages/dashboard && pnpm test && cd ../..
          
          echo -e "${GREEN}✓ All tests passed!${NC}"
          ;;
          
      lint)
          print_header "🔍 Running Linters"
          
          echo -e "${YELLOW}Linting Python...${NC}"
          cd packages/api && poetry run ruff check . && cd ../..
          cd packages/sdk-python && poetry run ruff check . && cd ../..
          
          echo -e "${YELLOW}Linting TypeScript...${NC}"
          cd packages/sdk-js && pnpm lint && cd ../..
          cd packages/dashboard && pnpm lint && cd ../..
          
          echo -e "${GREEN}✓ Linting complete${NC}"
          ;;
          
      clean)
          print_header "🧹 Cleaning Up"
          docker-compose down -v --remove-orphans
          rm -rf packages/api/.venv
          rm -rf packages/sdk-python/.venv
          rm -rf packages/dashboard/node_modules
          rm -rf packages/sdk-js/node_modules
          rm -rf packages/dashboard/.next
          echo -e "${GREEN}✓ Cleanup complete${NC}"
          ;;
          
      db:migrate)
          print_header "🗄️ Running Database Migrations"
          cd packages/api && poetry run alembic upgrade head && cd ../..
          echo -e "${GREEN}✓ Migrations complete${NC}"
          ;;
          
      db:reset)
          print_header "🗄️ Resetting Database"
          echo -e "${RED}WARNING: This will delete all data!${NC}"
          read -p "Are you sure? (y/N) " -n 1 -r
          echo
          if [[ $REPLY =~ ^[Yy]$ ]]; then
              docker-compose down -v
              docker-compose up -d supabase-db
              sleep 5
              cd packages/api && poetry run alembic upgrade head && cd ../..
              echo -e "${GREEN}✓ Database reset complete${NC}"
          fi
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
          echo "  db:migrate  Run database migrations"
          echo "  db:reset    Reset database (DESTRUCTIVE)"
          ;;
  esac
  EOF
  
  chmod +x scripts/dev.sh
  ```

- [ ] **1.2.3.3** Create `scripts/release.sh`
  ```bash
  cat > scripts/release.sh << 'EOF'
  #!/bin/bash
  set -e
  
  # Release script for CodeWarden
  # Usage: ./scripts/release.sh [major|minor|patch]
  
  VERSION_TYPE=${1:-patch}
  
  echo "🚀 Creating $VERSION_TYPE release..."
  
  # Ensure we're on main branch
  CURRENT_BRANCH=$(git branch --show-current)
  if [ "$CURRENT_BRANCH" != "main" ]; then
      echo "❌ Must be on main branch to release"
      exit 1
  fi
  
  # Ensure working directory is clean
  if [ -n "$(git status --porcelain)" ]; then
      echo "❌ Working directory must be clean"
      exit 1
  fi
  
  # Get current version
  CURRENT_VERSION=$(cat VERSION)
  echo "Current version: $CURRENT_VERSION"
  
  # Calculate new version
  IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
  MAJOR=${VERSION_PARTS[0]}
  MINOR=${VERSION_PARTS[1]}
  PATCH=${VERSION_PARTS[2]}
  
  case $VERSION_TYPE in
      major)
          MAJOR=$((MAJOR + 1))
          MINOR=0
          PATCH=0
          ;;
      minor)
          MINOR=$((MINOR + 1))
          PATCH=0
          ;;
      patch)
          PATCH=$((PATCH + 1))
          ;;
  esac
  
  NEW_VERSION="$MAJOR.$MINOR.$PATCH"
  echo "New version: $NEW_VERSION"
  
  # Update VERSION file
  echo "$NEW_VERSION" > VERSION
  
  # Update package versions
  cd packages/sdk-python
  poetry version $NEW_VERSION
  cd ../..
  
  cd packages/sdk-js
  npm version $NEW_VERSION --no-git-tag-version
  cd ../..
  
  cd packages/api
  poetry version $NEW_VERSION
  cd ../..
  
  # Commit and tag
  git add .
  git commit -m "chore: release v$NEW_VERSION"
  git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"
  
  echo "✅ Release v$NEW_VERSION created"
  echo ""
  echo "To publish:"
  echo "  git push origin main --tags"
  EOF
  
  chmod +x scripts/release.sh
  ```

- [ ] **1.2.3.4** Create `VERSION` file
  ```bash
  echo "0.1.0" > VERSION
  ```

**Testing:**
- [ ] Run `./scripts/dev.sh` → Shows help message
- [ ] Run `ls -la scripts/` → All scripts are executable

---

### Task 1.2.4: Create Docker Configuration

**Sub-tasks:**

- [ ] **1.2.4.1** Create `docker-compose.yml`
  ```bash
  cat > docker-compose.yml << 'EOF'
  version: '3.8'
  
  services:
    # ═══════════════════════════════════════════════════════════════
    # DATABASE LAYER
    # ═══════════════════════════════════════════════════════════════
    
    supabase-db:
      image: supabase/postgres:15.1.0.117
      container_name: codewarden-db
      ports:
        - "5432:5432"
      environment:
        POSTGRES_USER: postgres
        POSTGRES_PASSWORD: postgres
        POSTGRES_DB: postgres
      volumes:
        - supabase-data:/var/lib/postgresql/data
        - ./infrastructure/sql/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
      healthcheck:
        test: ["CMD-SHELL", "pg_isready -U postgres"]
        interval: 10s
        timeout: 5s
        retries: 5
      restart: unless-stopped
    
    # ═══════════════════════════════════════════════════════════════
    # CACHE / QUEUE LAYER
    # ═══════════════════════════════════════════════════════════════
    
    redis:
      image: redis:7-alpine
      container_name: codewarden-redis
      ports:
        - "6379:6379"
      volumes:
        - redis-data:/data
      command: redis-server --appendonly yes
      healthcheck:
        test: ["CMD", "redis-cli", "ping"]
        interval: 10s
        timeout: 5s
        retries: 5
      restart: unless-stopped
    
    # ═══════════════════════════════════════════════════════════════
    # LOG STORAGE
    # ═══════════════════════════════════════════════════════════════
    
    openobserve:
      image: openobserve/openobserve:latest
      container_name: codewarden-openobserve
      ports:
        - "5080:5080"
      environment:
        ZO_ROOT_USER_EMAIL: admin@codewarden.local
        ZO_ROOT_USER_PASSWORD: admin123
        ZO_DATA_DIR: /data
      volumes:
        - openobserve-data:/data
      healthcheck:
        test: ["CMD", "curl", "-f", "http://localhost:5080/healthz"]
        interval: 30s
        timeout: 10s
        retries: 5
      restart: unless-stopped
    
    # ═══════════════════════════════════════════════════════════════
    # APPLICATION LAYER
    # ═══════════════════════════════════════════════════════════════
    
    api:
      build:
        context: ./packages/api
        dockerfile: Dockerfile
      container_name: codewarden-api
      ports:
        - "8000:8000"
      environment:
        - ENVIRONMENT=development
        - DATABASE_URL=postgresql://postgres:postgres@supabase-db:5432/postgres
        - REDIS_URL=redis://redis:6379
        - OPENOBSERVE_URL=http://openobserve:5080
        - GOOGLE_API_KEY=${GOOGLE_API_KEY}
        - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
        - OPENAI_API_KEY=${OPENAI_API_KEY}
        - RESEND_API_KEY=${RESEND_API_KEY}
        - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      depends_on:
        supabase-db:
          condition: service_healthy
        redis:
          condition: service_healthy
        openobserve:
          condition: service_healthy
      volumes:
        - ./packages/api:/app
        - /app/.venv
      command: poetry run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
      restart: unless-stopped
    
    api-worker:
      build:
        context: ./packages/api
        dockerfile: Dockerfile
      container_name: codewarden-worker
      environment:
        - ENVIRONMENT=development
        - DATABASE_URL=postgresql://postgres:postgres@supabase-db:5432/postgres
        - REDIS_URL=redis://redis:6379
        - OPENOBSERVE_URL=http://openobserve:5080
        - GOOGLE_API_KEY=${GOOGLE_API_KEY}
        - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
        - OPENAI_API_KEY=${OPENAI_API_KEY}
        - RESEND_API_KEY=${RESEND_API_KEY}
      depends_on:
        - api
      volumes:
        - ./packages/api:/app
        - /app/.venv
      command: poetry run arq api.workers.settings.WorkerSettings
      restart: unless-stopped
    
    dashboard:
      build:
        context: ./packages/dashboard
        dockerfile: Dockerfile.dev
      container_name: codewarden-dashboard
      ports:
        - "3000:3000"
      environment:
        - NEXT_PUBLIC_API_URL=http://localhost:8000
        - NEXT_PUBLIC_SUPABASE_URL=http://localhost:8000
      volumes:
        - ./packages/dashboard:/app
        - /app/node_modules
        - /app/.next
      command: pnpm dev
      restart: unless-stopped
  
  volumes:
    supabase-data:
    redis-data:
    openobserve-data:
  
  networks:
    default:
      name: codewarden-network
  EOF
  ```

- [ ] **1.2.4.2** Create database init script
  ```bash
  mkdir -p infrastructure/sql
  
  cat > infrastructure/sql/init.sql << 'EOF'
  -- CodeWarden Database Initialization Script
  -- This runs automatically when the container first starts
  
  -- Enable UUID extension
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
  
  -- Create test database for tests
  CREATE DATABASE postgres_test;
  
  -- Grant permissions
  GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
  GRANT ALL PRIVILEGES ON DATABASE postgres_test TO postgres;
  EOF
  ```

**Testing:**
- [ ] Run `docker-compose config` → No errors
- [ ] Run `docker-compose up -d supabase-db redis` → Services start
- [ ] Run `docker-compose ps` → Shows running services

---

## Story 1.3: GitHub Configuration

### Task 1.3.1: Create GitHub Workflows

**Sub-tasks:**

- [ ] **1.3.1.1** Create CI workflow
  ```bash
  cat > .github/workflows/ci.yml << 'EOF'
  name: CI
  
  on:
    push:
      branches: [main, develop]
    pull_request:
      branches: [main]
  
  env:
    PYTHON_VERSION: '3.11'
    NODE_VERSION: '20'
  
  jobs:
    # ─────────────────────────────────────────────────────────────
    # LINT ALL PACKAGES
    # ─────────────────────────────────────────────────────────────
    lint:
      name: Lint
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        
        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: ${{ env.PYTHON_VERSION }}
        
        - name: Set up Node.js
          uses: actions/setup-node@v4
          with:
            node-version: ${{ env.NODE_VERSION }}
        
        - name: Install Poetry
          run: pip install poetry
        
        - name: Install pnpm
          run: npm install -g pnpm
        
        - name: Lint Python (API)
          working-directory: packages/api
          run: |
            poetry install --only dev
            poetry run ruff check .
        
        - name: Lint Python (SDK)
          working-directory: packages/sdk-python
          run: |
            poetry install --only dev
            poetry run ruff check .
        
        - name: Lint TypeScript (SDK)
          working-directory: packages/sdk-js
          run: |
            pnpm install
            pnpm lint
        
        - name: Lint TypeScript (Dashboard)
          working-directory: packages/dashboard
          run: |
            pnpm install
            pnpm lint
  
    # ─────────────────────────────────────────────────────────────
    # TEST API
    # ─────────────────────────────────────────────────────────────
    test-api:
      name: Test API
      runs-on: ubuntu-latest
      needs: lint
      
      services:
        postgres:
          image: postgres:15
          env:
            POSTGRES_USER: postgres
            POSTGRES_PASSWORD: postgres
            POSTGRES_DB: postgres_test
          ports:
            - 5432:5432
          options: >-
            --health-cmd pg_isready
            --health-interval 10s
            --health-timeout 5s
            --health-retries 5
        
        redis:
          image: redis:7-alpine
          ports:
            - 6379:6379
          options: >-
            --health-cmd "redis-cli ping"
            --health-interval 10s
            --health-timeout 5s
            --health-retries 5
      
      steps:
        - uses: actions/checkout@v4
        
        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: ${{ env.PYTHON_VERSION }}
        
        - name: Install Poetry
          run: pip install poetry
        
        - name: Install dependencies
          working-directory: packages/api
          run: poetry install
        
        - name: Run tests
          working-directory: packages/api
          env:
            DATABASE_URL: postgresql://postgres:postgres@localhost:5432/postgres_test
            REDIS_URL: redis://localhost:6379
            ENVIRONMENT: test
          run: poetry run pytest --cov=api --cov-report=xml -v
        
        - name: Upload coverage
          uses: codecov/codecov-action@v3
          with:
            files: packages/api/coverage.xml
            flags: api
  
    # ─────────────────────────────────────────────────────────────
    # TEST PYTHON SDK
    # ─────────────────────────────────────────────────────────────
    test-sdk-python:
      name: Test Python SDK
      runs-on: ubuntu-latest
      needs: lint
      
      steps:
        - uses: actions/checkout@v4
        
        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: ${{ env.PYTHON_VERSION }}
        
        - name: Install Poetry
          run: pip install poetry
        
        - name: Install dependencies
          working-directory: packages/sdk-python
          run: poetry install
        
        - name: Run tests
          working-directory: packages/sdk-python
          run: poetry run pytest --cov=codewarden --cov-report=xml -v
        
        - name: Upload coverage
          uses: codecov/codecov-action@v3
          with:
            files: packages/sdk-python/coverage.xml
            flags: sdk-python
  
    # ─────────────────────────────────────────────────────────────
    # TEST JAVASCRIPT SDK
    # ─────────────────────────────────────────────────────────────
    test-sdk-js:
      name: Test JavaScript SDK
      runs-on: ubuntu-latest
      needs: lint
      
      steps:
        - uses: actions/checkout@v4
        
        - name: Set up Node.js
          uses: actions/setup-node@v4
          with:
            node-version: ${{ env.NODE_VERSION }}
        
        - name: Install pnpm
          run: npm install -g pnpm
        
        - name: Install dependencies
          working-directory: packages/sdk-js
          run: pnpm install
        
        - name: Run tests
          working-directory: packages/sdk-js
          run: pnpm test:coverage
  
    # ─────────────────────────────────────────────────────────────
    # BUILD DASHBOARD
    # ─────────────────────────────────────────────────────────────
    build-dashboard:
      name: Build Dashboard
      runs-on: ubuntu-latest
      needs: lint
      
      steps:
        - uses: actions/checkout@v4
        
        - name: Set up Node.js
          uses: actions/setup-node@v4
          with:
            node-version: ${{ env.NODE_VERSION }}
        
        - name: Install pnpm
          run: npm install -g pnpm
        
        - name: Install dependencies
          working-directory: packages/dashboard
          run: pnpm install
        
        - name: Build
          working-directory: packages/dashboard
          env:
            NEXT_PUBLIC_API_URL: https://api.codewarden.io
          run: pnpm build
  EOF
  ```

- [ ] **1.3.1.2** Create deploy workflow
  ```bash
  cat > .github/workflows/deploy.yml << 'EOF'
  name: Deploy
  
  on:
    push:
      branches: [main]
    workflow_dispatch:
  
  jobs:
    # ─────────────────────────────────────────────────────────────
    # DEPLOY API TO RAILWAY
    # ─────────────────────────────────────────────────────────────
    deploy-api:
      name: Deploy API
      runs-on: ubuntu-latest
      if: github.ref == 'refs/heads/main'
      
      steps:
        - uses: actions/checkout@v4
        
        - name: Deploy to Railway
          uses: bervProject/railway-deploy@main
          with:
            railway_token: ${{ secrets.RAILWAY_TOKEN }}
            service: codewarden-api
  
    # ─────────────────────────────────────────────────────────────
    # DEPLOY DASHBOARD TO VERCEL
    # ─────────────────────────────────────────────────────────────
    deploy-dashboard:
      name: Deploy Dashboard
      runs-on: ubuntu-latest
      if: github.ref == 'refs/heads/main'
      
      steps:
        - uses: actions/checkout@v4
        
        - name: Deploy to Vercel
          uses: amondnet/vercel-action@v25
          with:
            vercel-token: ${{ secrets.VERCEL_TOKEN }}
            vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
            vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
            vercel-args: '--prod'
            working-directory: packages/dashboard
  EOF
  ```

- [ ] **1.3.1.3** Create SDK publish workflow
  ```bash
  cat > .github/workflows/publish-sdk.yml << 'EOF'
  name: Publish SDKs
  
  on:
    release:
      types: [published]
  
  jobs:
    # ─────────────────────────────────────────────────────────────
    # PUBLISH PYTHON SDK TO PYPI
    # ─────────────────────────────────────────────────────────────
    publish-python:
      name: Publish to PyPI
      runs-on: ubuntu-latest
      
      steps:
        - uses: actions/checkout@v4
        
        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: '3.11'
        
        - name: Install Poetry
          run: pip install poetry
        
        - name: Build package
          working-directory: packages/sdk-python
          run: poetry build
        
        - name: Publish to PyPI
          working-directory: packages/sdk-python
          env:
            POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_TOKEN }}
          run: poetry publish
  
    # ─────────────────────────────────────────────────────────────
    # PUBLISH JS SDK TO NPM
    # ─────────────────────────────────────────────────────────────
    publish-npm:
      name: Publish to NPM
      runs-on: ubuntu-latest
      
      steps:
        - uses: actions/checkout@v4
        
        - name: Set up Node.js
          uses: actions/setup-node@v4
          with:
            node-version: '20'
            registry-url: 'https://registry.npmjs.org'
        
        - name: Install pnpm
          run: npm install -g pnpm
        
        - name: Install dependencies
          working-directory: packages/sdk-js
          run: pnpm install
        
        - name: Build
          working-directory: packages/sdk-js
          run: pnpm build
        
        - name: Publish to NPM
          working-directory: packages/sdk-js
          env:
            NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
          run: npm publish
  EOF
  ```

- [ ] **1.3.1.4** Create CODEOWNERS file
  ```bash
  cat > .github/CODEOWNERS << 'EOF'
  # Default owners for everything
  * @your-username
  
  # API
  /packages/api/ @your-username
  
  # Dashboard
  /packages/dashboard/ @your-username
  
  # SDKs
  /packages/sdk-python/ @your-username
  /packages/sdk-js/ @your-username
  
  # Infrastructure
  /infrastructure/ @your-username
  /.github/ @your-username
  EOF
  ```

- [ ] **1.3.1.5** Create PR template
  ```bash
  mkdir -p .github
  
  cat > .github/pull_request_template.md << 'EOF'
  ## Description
  
  Brief description of changes.
  
  ## Type of Change
  
  - [ ] 🐛 Bug fix
  - [ ] ✨ New feature
  - [ ] 🔧 Refactor
  - [ ] 📝 Documentation
  - [ ] 🔒 Security fix
  
  ## Checklist
  
  - [ ] Tests pass locally (`./scripts/dev.sh test`)
  - [ ] Lint passes (`./scripts/dev.sh lint`)
  - [ ] Documentation updated (if needed)
  - [ ] Breaking changes documented
  
  ## Related Issues
  
  Closes #
  
  ## Screenshots (if applicable)
  
  EOF
  ```

**Testing:**
- [ ] Review `.github/workflows/ci.yml` → Valid YAML
- [ ] Review `.github/workflows/deploy.yml` → Valid YAML

---

### Task 1.3.2: Configure GitHub Repository Settings

**Sub-tasks:**

- [ ] **1.3.2.1** Enable branch protection
  ```
  Settings → Branches → Add rule
  
  Branch name pattern: main
  
  ✅ Require a pull request before merging
    ✅ Require approvals (1)
  ✅ Require status checks to pass before merging
    ✅ Require branches to be up to date before merging
    Status checks:
      - lint
      - test-api
      - test-sdk-python
      - test-sdk-js
      - build-dashboard
  ✅ Require conversation resolution before merging
  ❌ Do not allow bypassing the above settings
  ```

- [ ] **1.3.2.2** Add repository secrets
  ```
  Settings → Secrets and variables → Actions → New repository secret
  
  Required secrets:
  - RAILWAY_TOKEN         (from Railway dashboard)
  - VERCEL_TOKEN         (from Vercel settings)
  - VERCEL_ORG_ID        (from Vercel project settings)
  - VERCEL_PROJECT_ID    (from Vercel project settings)
  - PYPI_TOKEN           (from PyPI account)
  - NPM_TOKEN            (from npm account)
  - CODECOV_TOKEN        (from Codecov)
  ```

- [ ] **1.3.2.3** Enable Dependabot
  ```bash
  cat > .github/dependabot.yml << 'EOF'
  version: 2
  updates:
    # Python dependencies
    - package-ecosystem: "pip"
      directory: "/packages/api"
      schedule:
        interval: "weekly"
      open-pull-requests-limit: 5
    
    - package-ecosystem: "pip"
      directory: "/packages/sdk-python"
      schedule:
        interval: "weekly"
      open-pull-requests-limit: 5
    
    # JavaScript dependencies
    - package-ecosystem: "npm"
      directory: "/packages/dashboard"
      schedule:
        interval: "weekly"
      open-pull-requests-limit: 5
    
    - package-ecosystem: "npm"
      directory: "/packages/sdk-js"
      schedule:
        interval: "weekly"
      open-pull-requests-limit: 5
    
    # GitHub Actions
    - package-ecosystem: "github-actions"
      directory: "/"
      schedule:
        interval: "weekly"
      open-pull-requests-limit: 5
  EOF
  ```

**Testing:**
- [ ] Create test PR → CI runs automatically
- [ ] Verify branch protection is enforced

---

## Story 1.4: External Service Setup

### Task 1.4.1: Create Supabase Project

**Sub-tasks:**

- [ ] **1.4.1.1** Create Supabase account and project
  ```
  1. Go to https://supabase.com
  2. Sign up / Log in
  3. Click "New Project"
  4. Project name: codewarden-production
  5. Database password: (generate strong password, save it!)
  6. Region: Choose closest to your users
  7. Click "Create new project"
  8. Wait for project to be ready (~2 minutes)
  ```

- [ ] **1.4.1.2** Get Supabase credentials
  ```
  Settings → Project Settings → API

  Save these values:
  - Project URL (SUPABASE_URL)

  NEW API Keys (2025+) - Use these for new projects:
  - publishable key (SUPABASE_PUBLISHABLE_KEY) - safe for frontend/browser
  - secret key (SUPABASE_SECRET_KEY) - KEEP SECRET! Backend only

  LEGACY API Keys (deprecated, will be removed):
  - anon key → replaced by publishable key
  - service_role key → replaced by secret key

  Settings → Database
  - Connection string (DATABASE_URL)

  NOTE: If your project was created before Nov 2025, you may still see
  the legacy keys. Migrate to new keys when possible.
  ```

- [ ] **1.4.1.3** Configure Supabase Auth
  ```
  Authentication → Providers
  
  ✅ Email (enabled by default)
    ✅ Enable email confirmations
    ✅ Enable magic link login
  
  Authentication → URL Configuration
  - Site URL: https://app.codewarden.io (or http://localhost:3000 for dev)
  - Redirect URLs:
    - http://localhost:3000/**
    - https://app.codewarden.io/**
  ```

**Testing:**
- [ ] Visit Supabase dashboard → Project is running
- [ ] Test database connection with credentials

---

### Task 1.4.2: Create Upstash Redis

**Sub-tasks:**

- [ ] **1.4.2.1** Create Upstash account and database
  ```
  1. Go to https://upstash.com
  2. Sign up / Log in
  3. Click "Create Database"
  4. Name: codewarden-redis
  5. Type: Regional
  6. Region: Choose closest to your API
  7. Click "Create"
  ```

- [ ] **1.4.2.2** Get Upstash credentials
  ```
  From database details page:
  
  Save these values:
  - UPSTASH_REDIS_REST_URL
  - UPSTASH_REDIS_REST_TOKEN
  
  Also available:
  - Standard Redis URL (for local testing with redis-cli)
  ```

**Testing:**
- [ ] Visit Upstash console → Database shows "Active"
- [ ] Run: `redis-cli -u <redis-url> ping` → Returns "PONG"

---

### Task 1.4.3: Setup AI Provider Accounts

**Sub-tasks:**

- [ ] **1.4.3.1** Get Google AI (Gemini) API Key
  ```
  1. Go to https://makersuite.google.com/app/apikey
  2. Sign in with Google account
  3. Click "Create API Key"
  4. Copy the key (GOOGLE_API_KEY)
  ```

- [ ] **1.4.3.2** Get Anthropic API Key
  ```
  1. Go to https://console.anthropic.com/
  2. Sign up / Log in
  3. Go to API Keys
  4. Create new key
  5. Copy the key (ANTHROPIC_API_KEY)
  ```

- [ ] **1.4.3.3** Get OpenAI API Key
  ```
  1. Go to https://platform.openai.com/api-keys
  2. Sign up / Log in
  3. Create new secret key
  4. Copy the key (OPENAI_API_KEY)
  ```

**Testing:**
- [ ] Test Gemini: `curl -H "x-goog-api-key: $GOOGLE_API_KEY" ...`
- [ ] Test each key works with a simple API call

---

### Task 1.4.4: Setup Notification Services

**Sub-tasks:**

- [ ] **1.4.4.1** Create Resend account
  ```
  1. Go to https://resend.com
  2. Sign up / Log in
  3. Go to API Keys
  4. Create new API key
  5. Copy the key (RESEND_API_KEY)
  
  6. Verify a domain (for production):
     - Add DNS records as shown
     - Wait for verification
  ```

- [ ] **1.4.4.2** Create Telegram Bot
  ```
  1. Open Telegram
  2. Search for @BotFather
  3. Send /newbot
  4. Name: CodeWarden Alerts
  5. Username: codewarden_bot (or available name)
  6. Copy the token (TELEGRAM_BOT_TOKEN)
  
  7. Customize bot:
     /setdescription - Add description
     /setabouttext - Add about text
     /setuserpic - Upload bot avatar
  ```

**Testing:**
- [ ] Resend: Send test email via dashboard
- [ ] Telegram: Send message to bot, verify it's received

---

### Task 1.4.5: Setup Cloudflare R2

**Sub-tasks:**

- [ ] **1.4.5.1** Create Cloudflare account and R2 bucket
  ```
  1. Go to https://dash.cloudflare.com
  2. Sign up / Log in
  3. Go to R2 → Create bucket
  4. Bucket name: codewarden-evidence
  5. Location: Automatic
  6. Click "Create bucket"
  ```

- [ ] **1.4.5.2** Create R2 API tokens
  ```
  R2 → Manage R2 API Tokens → Create API token
  
  Permissions: Object Read & Write
  Specify bucket: codewarden-evidence
  TTL: No expiration
  
  Save:
  - Access Key ID (CLOUDFLARE_R2_ACCESS_KEY_ID)
  - Secret Access Key (CLOUDFLARE_R2_SECRET_ACCESS_KEY)
  - Endpoint URL (CLOUDFLARE_R2_ENDPOINT)
  ```

**Testing:**
- [ ] Use S3-compatible tool to list bucket (should be empty)

---

## Phase 1 Completion Checklist

### Infrastructure Ready
- [ ] Local development tools installed
- [ ] Monorepo structure created
- [ ] Docker Compose working
- [ ] GitHub repository configured
- [ ] CI/CD pipelines created

### External Services Ready
- [ ] Supabase project created and configured
- [ ] Upstash Redis database created
- [ ] Google AI API key obtained
- [ ] Anthropic API key obtained
- [ ] OpenAI API key obtained
- [ ] Resend account configured
- [ ] Telegram bot created
- [ ] Cloudflare R2 bucket created

### Environment Files
- [ ] `.env.example` complete with all variables
- [ ] `.env` created with actual values
- [ ] All secrets added to GitHub repository

### Verification Tests
- [ ] `./scripts/dev.sh start` → All services running
- [ ] Docker containers healthy
- [ ] Can connect to local Postgres
- [ ] Can connect to local Redis
- [ ] OpenObserve accessible at localhost:5080

---

## Next Steps

Proceed to **Part 2: Core Product Development** which covers:
- Python SDK implementation
- API development
- AI integration
- Database schema and migrations

---

**Document Control:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2026 | Engineering | Initial release |
