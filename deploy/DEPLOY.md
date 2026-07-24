# HiveOS Deployment Guide

> **ADR-0008**: On-premise default. All data stays on customer infrastructure.

## Prerequisites

- Docker 20.10+ and Docker Compose v2
- 2GB RAM minimum (4GB recommended)
- 1GB disk space for container + data

## Quick Start

```bash
# Clone the repo
git clone https://github.com/hossein1377mobini/hiveos-financial-brain.git
cd hiveos-financial-brain

# Build and start
docker compose up -d

# Check status
docker compose ps
docker compose logs -f hiveos
```

Open **http://localhost:8080** in your browser.

## Architecture

```
┌─────────────────────────────────────┐
│           Docker Container          │
│  ┌───────────────────────────────┐  │
│  │  Python 3.11 + HiveOS 0.12.0 │  │
│  │  FastAPI + Uvicorn            │  │
│  │  SQLite (WAL mode)            │  │
│  └───────────────┬───────────────┘  │
│                  │                  │
│  ┌───────────────▼───────────────┐  │
│  │  Dashboard (SPA) + Playground │  │
│  │  React Flow Visual Builder    │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
         │                │
    ┌────▼────┐    ┌──────▼──────┐
    │  :8080  │    │ /data vol   │
    │  HTTP   │    │ (SQLite +   │
    └─────────┘    │  state)     │
                   └─────────────┘
```

## Data Persistence

All data persists in a Docker named volume (`hiveos-data`):

| Data | Location | Description |
|------|----------|-------------|
| Database | `/data/hiveos.db` | Brain, Learning, Playground state |
| Config | `/data/config/` | Workspace config |
| Domains | `/data/domains/` | Installed domain packs |

### Backup & Restore

```bash
# Backup
docker run --rm -v hiveos-data:/data -v $(pwd):/backup alpine \
    tar czf /backup/hiveos-backup-$(date +%Y%m%d).tar.gz -C /data .

# Restore
docker run --rm -v hiveos-data:/data -v $(pwd):/backup alpine \
    tar xzf /backup/hiveos-backup-20260724.tar.gz -C /data
```

## Configuration

Environment variables (set in `docker-compose.yml` or `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `HIVEOS_HOST` | `0.0.0.0` | Bind address |
| `HIVEOS_PORT` | `8080` | HTTP port |
| `HIVEOS_DATA_DIR` | `/data` | Data directory inside container |

## Production Setup

### With Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name hiveos.example.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Systemd Service

```ini
[Unit]
Description=HiveOS Multi-Agent Operating System
After=docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=/opt/hiveos
ExecStart=/usr/bin/docker compose up
ExecStop=/usr/bin/docker compose down
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## CLI Access

```bash
# Open a shell inside the container
docker exec -it hiveos /bin/bash

# Run HiveOS CLI commands
docker exec -it hiveos hive --version
docker exec -it hiveos hive dashboard status
docker exec -it hiveos hive domain list
```

## Networking

The container binds to `0.0.0.0:8080` by default (ADR-0008: accessible on the network for management). To restrict access:

```yaml
# docker-compose.yml — bind to localhost only
ports:
  - "127.0.0.1:8080:8080"
```

## Air-Gapped Environments

HiveOS works fully offline. For air-gapped deployment:

1. Build on a connected machine: `docker compose build`
2. Export the image: `docker save hiveos -o hiveos.tar`
3. Transfer and load: `docker load -i hiveos.tar`
4. Run normally: `docker compose up -d`

No cloud AI provider is required for core functionality.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Port already in use | Change `HIVEOS_PORT` in `.env` or `docker-compose.yml` |
| Permission denied on data | `docker compose down && sudo chown -R 1000:1000 ./hiveos-data` |
| Container won't start | `docker compose logs hiveos` — check for import errors |
| Slow startup | First run initializes SQLite — 10-15s is normal |

## Updating

```bash
docker compose down
git pull origin main
docker compose build --no-cache
docker compose up -d
```

Data persists across updates via the named volume.
