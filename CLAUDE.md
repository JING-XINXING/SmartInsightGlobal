# CLAUDE.md - SmartInsight Global Project Guide

## Commands
- **Backend (Python)**:
  - Install: `pip install -r requirements.txt`
  - Run Dev: `uvicorn app.main:app --reload`
  - Test: `pytest`
  - Lint: `flake8 .`
- **Frontend (Next.js/React)**:
  - Install: `npm install`
  - Run Dev: `npm run dev`
  - Build: `npm run build`
  - Lint: `npm run lint`
- **Infrastructure**:
  - Start All: `docker-compose up -d`
  - Stop All: `docker-compose down`
  - DB Shell: `docker-compose exec db psql -U user -d smartinsight`

## Tech Stack
- **Backend**: Python 3.10+ (FastAPI) OR Go (Gin)
- **Frontend**: Next.js (React), TailwindCSS, Shadcn/UI
- **Database**: PostgreSQL (JSONB), Redis (Cache/Queue)
- **AI**: Domestic Multi-modal LLM APIs (DeepSeek, Qwen, Yi, GLM)
- **Storage**: Local FS + Object Storage (OSS/S3)

## Code Style Guidelines
- **Python**: Follow PEP 8. Use type hints (`typing`). Async/await for I/O.
- **JavaScript/TypeScript**: Functional components. Hooks for state. Async/await.
- **Naming**: `snake_case` for Python variables/functions, `CamelCase` for Classes. `camelCase` for JS/TS variables, `PascalCase` for Components.
- **Error Handling**: Graceful degradation. Log errors to file/stdout.
- **Comments**: Docstrings for all public modules/functions.

## Architecture
- **Data Collection**: `crawlers/` (RSS, API, Scrapers). Respect `robots.txt`.
- **Analysis**: `analysis/` (LLM Clients, Prompt Templates).
- **Storage**: `database/` (Models, Migrations).
- **Backup**: `scripts/backup/` (Local & Cloud sync).
