#!/bin/sh
# ── HiveOS Docker Entrypoint ──────────────────────────────────────
# ADR-0008: on-premise default — binds 0.0.0.0 for container access.
# Uses V2 Dashboard (HiveOSApp factory, uvicorn).
# ──────────────────────────────────────────────────────────────────
set -e

HOST="${HIVEOS_HOST:-0.0.0.0}"
PORT="${HIVEOS_PORT:-8080}"
DATA_DIR="${HIVEOS_DATA_DIR:-/data}"

VERSION=$(python -c 'from hiveos import __version__; print(__version__)' 2>/dev/null || echo "dev")

echo "========================================"
echo "  HiveOS — Organizational Intelligence"
echo "  Version: ${VERSION}"
echo "========================================"
echo ""
echo "  Host:     ${HOST}"
echo "  Port:     ${PORT}"
echo "  Data:     ${DATA_DIR}"
echo ""

# Initialize data directory if needed
mkdir -p "${DATA_DIR}"

# Launch V2 Dashboard via uvicorn factory
exec python -m uvicorn \
    hiveos.dashboard.app:create_app \
    --factory \
    --host "${HOST}" \
    --port "${PORT}" \
    --log-level info
