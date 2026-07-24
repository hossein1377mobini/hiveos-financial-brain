# ── HiveOS Dockerfile ──────────────────────────────────────────────
# Multi-stage: Python 3.11 slim, playground pre-built in repo.
# ADR-0008: on-premise default — no cloud dependency for core.
#
# Build:  docker build -t hiveos .
# Run:    docker run -p 8080:8080 -v hiveos-data:/data hiveos
# ──────────────────────────────────────────────────────────────────

# ── Stage 1: Build wheel ──────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install .

# ── Stage 2: Runtime ──────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="HiveOS Team"
LABEL description="HiveOS — Multi-Agent Operating System (on-premise)"
LABEL org.opencontainers.image.source="https://github.com/hossein1377mobini/hiveos-financial-brain"

# Non-root user for security
RUN groupadd -r hiveos && useradd -r -g hiveos -d /home/hiveos -s /sbin/nologin hiveos

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy source (templates, prompts, domain blueprints — everything at runtime)
COPY src/ /opt/hiveos/src/

# Copy CLI entrypoint helper
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Data directory — mounted as volume for persistence
RUN mkdir -p /data && chown -R hiveos:hiveos /data

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HIVEOS_HOST=0.0.0.0 \
    HIVEOS_PORT=8080 \
    HIVEOS_DATA_DIR=/data

EXPOSE 8080

VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

USER hiveos
WORKDIR /home/hiveos

ENTRYPOINT ["/entrypoint.sh"]
