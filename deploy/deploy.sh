#!/bin/sh
# ── HiveOS Deploy.sh ───────────────────────────────────────────────
# One-liner VPS deployment: clones, builds, starts HiveOS.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/hossein1377mobini/hiveos-financial-brain/main/deploy.sh | sh
#
# Or (from local repo):
#   ./deploy.sh
#
# ADR-0008: on-premise default — runs locally with Docker.
# ──────────────────────────────────────────────────────────────────
set -e

REPO_URL="https://github.com/hossein1377mobini/hiveos-financial-brain.git"
INSTALL_DIR="${INSTALL_DIR:-/opt/hiveos}"
COMPOSE_FILE="${INSTALL_DIR}/docker-compose.yml"

echo "========================================"
echo "  HiveOS — On-Premise Installer"
echo "========================================"
echo ""

# ── Check prerequisites ──────────────────────────────────────────
command -v docker >/dev/null 2>&1 || {
    echo "ERROR: Docker not found. Install Docker first."
    echo "  https://docs.docker.com/engine/install/"
    exit 1
}
docker compose version >/dev/null 2>&1 || {
    echo "ERROR: Docker Compose v2 not found."
    exit 1
}

# ── Clone or pull ────────────────────────────────────────────────
if [ -d "${INSTALL_DIR}/.git" ]; then
    echo "→ Updating existing installation..."
    cd "${INSTALL_DIR}"
    git pull
else
    echo "→ Cloning to ${INSTALL_DIR}..."
    git clone "${REPO_URL}" "${INSTALL_DIR}"
    cd "${INSTALL_DIR}"
fi

# ── Build and start ──────────────────────────────────────────────
echo "→ Building Docker image..."
docker compose build

echo "→ Starting HiveOS..."
docker compose up -d

echo ""
echo "========================================"
echo "  HiveOS is running!"
echo "  Open: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8080"
echo "========================================"
echo ""
echo "Manage:"
echo "  docker compose logs -f       # tail logs"
echo "  docker compose down          # stop"
echo "  docker compose pull          # update"
echo "  ./deploy.sh                  # re-run to update"
