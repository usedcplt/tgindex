# TGIndex

Fully automated Telegram chat/channel indexing system.

## Overview

TGIndex is a search engine for public Telegram chats and channels. It automatically discovers new public Telegram groups and channels, extracts their metadata, stores information in PostgreSQL, maintains the index in up-to-date state with minimal load, and provides fast search via API and Web Dashboard.

**This is NOT a message archiver.** It's a search system for Telegram.

## Features

- Automatic discovery of new public Telegram chats and channels
- Metadata extraction (name, description, members, type, etc.)
- PostgreSQL Full-Text Search
- REST API
- Web Dashboard with auto-refresh
- Fully async architecture
- Optimized for low-resource VPS (500MB RAM, 0.1 vCPU)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DISCOVERY LAYER                         │
│  SearchEngineSource │ CatalogSource │ GitHubSource │ ...    │
└──────────────────────────┬──────────────────────────────────┘
                           │ Raw URLs
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     PROCESSING LAYER                        │
│  Normalizer → Deduplicator → Queue → Validator              │
└──────────────────────────┬──────────────────────────────────┘
                           │ Validated entities
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     TELEGRAM LAYER                          │
│  MetadataExtractor → Classifier → RateLimiter               │
└──────────────────────────┬──────────────────────────────────┘
                           │ Enriched entities
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     STORAGE LAYER                           │
│  Repository → PostgreSQL (Neon) → FTS Index                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     SERVING LAYER                           │
│  API (FastAPI) │ Dashboard (Jinja2 + HTMX)                 │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

- Python 3.11
- Telethon (Telegram API)
- FastAPI (API)
- SQLAlchemy 2.0 (ORM)
- PostgreSQL (Neon Console)
- Alembic (Migrations)
- APScheduler (Task scheduling)
- Jinja2 + HTMX (Dashboard)

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL database (e.g., Neon Console)
- Telegram API credentials (api_id, api_hash)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd tgindex
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -e .
```

4. Configure environment:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname
```

5. Run migrations:
```bash
alembic upgrade head
```

6. Start the server:
```bash
python -m app.main
```

The API will be available at `http://localhost:8000`
The Dashboard will be available at `http://localhost:8000/dashboard`

## API Endpoints

### Search
```
GET /api/v1/search?q=python&type=channel&language=ru&page=1&size=20
```

### Chats
```
GET /api/v1/chats                    # List all chats
GET /api/v1/chats/{telegram_id}      # Get chat by Telegram ID
```

### Statistics
```
GET /api/v1/statistics               # Get statistics
GET /api/v1/statistics/sources       # Get source statistics
GET /api/v1/statistics/history       # Get historical statistics
```

### Sources
```
GET /api/v1/sources                  # List all sources
POST /api/v1/sources/{id}/run        # Trigger source run
```

### System
```
GET /api/v1/system/health            # Health check
GET /api/v1/system/metrics           # System metrics
```

## Dashboard

The dashboard provides a web interface for:
- Overview of indexed chats
- Browsing and searching chats
- Managing discovery sources
- Viewing statistics and growth charts
- Monitoring system status

## Deployment

### Render.com

The project includes `render.yaml` for easy deployment to Render.com:

1. Push to GitHub
2. Connect repository to Render.com
3. Create a new Blueprint from the repository
4. Set environment variables in Render dashboard

### Manual Deployment

1. Set up PostgreSQL database
2. Configure environment variables
3. Run migrations: `alembic upgrade head`
4. Start the API server: `python -m app.main`
5. Start the worker: `python -m app.cli.commands worker`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_API_ID` | Telegram API ID | Required |
| `TELEGRAM_API_HASH` | Telegram API hash | Required |
| `DATABASE_URL` | PostgreSQL connection URL | Required |
| `APP_NAME` | Application name | TGIndex |
| `DEBUG` | Debug mode | false |
| `LOG_LEVEL` | Log level | INFO |
| `API_HOST` | API host | 0.0.0.0 |
| `API_PORT` | API port | 8000 |
| `CRAWL_BATCH_SIZE` | Batch size for processing | 50 |
| `DISCOVERY_INTERVAL_HOURS` | Discovery interval | 1 |
| `VALIDATION_INTERVAL_MINUTES` | Validation interval | 5 |

### Rate Limiting

The system implements token bucket rate limiting for Telegram API calls:
- Default: 1 request per second
- FloodWait handling with exponential backoff
- Configurable via `TELEGRAM_MAX_REQUESTS_PER_SECOND`

## Database Schema

### Tables

- `chats` - Main table for indexed Telegram chats/channels
- `discovery_sources` - Configuration for discovery sources
- `url_queue` - URL processing queue
- `crawl_logs` - Crawl history logs
- `statistics_snapshots` - Daily statistics snapshots

### Indexes

- Full-text search index on title, description, topic
- Indexes for common queries (username, type, language)
- Partial indexes for performance optimization

## Development

### Project Structure

```
tgindex/
├── app/
│   ├── api/           # REST API endpoints
│   ├── crawler/       # Discovery sources
│   ├── dashboard/     # Web dashboard
│   ├── database/      # Database configuration
│   ├── models/        # SQLAlchemy models
│   ├── repositories/  # Data access layer
│   ├── scheduler/     # Task scheduling
│   ├── services/      # Business logic
│   ├── telegram/      # Telegram API integration
│   ├── utils/         # Utility functions
│   └── workers/       # Background workers
├── migrations/        # Alembic migrations
├── tests/            # Test suite
└── docs/             # Documentation
```

### Adding New Discovery Source

1. Create a new class in `app/crawler/`
2. Inherit from `BaseSource`
3. Implement the `discover()` method
4. Register the source in `app/crawler/__init__.py`

Example:
```python
from app.crawler.base_source import BaseSource

class MySource(BaseSource):
    async def discover(self) -> list[str]:
        # Your discovery logic here
        return ["https://t.me/example"]
```

## License

MIT
