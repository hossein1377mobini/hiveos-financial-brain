"""Docker container smoke tests — validates build, health, endpoints."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def run_container():
    """Build and run HiveOS container, return healthcheck results."""
    project_root = Path(__file__).resolve().parent.parent
    container_name = "hiveos-smoke-test"

    # Clean up any leftover container
    subprocess.run(
        ["docker", "rm", "-f", container_name],
        capture_output=True,
    )

    # Build
    result = subprocess.run(
        ["docker", "build", "-t", "hiveos-smoke", str(project_root)],
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, f"Build failed:\n{result.stderr}"

    # Run
    subprocess.run(
        [
            "docker", "run", "-d",
            "--name", container_name,
            "-p", "18081:8080",
            "-v", f"{container_name}-data:/data",
            "hiveos-smoke",
        ],
        capture_output=True, timeout=30,
    )

    # Wait for health
    healthy = False
    for _ in range(30):
        time.sleep(2)
        # Check container status
        ps = subprocess.run(
            ["docker", "inspect", container_name, "--format", "{{.State.Health.Status}}"],
            capture_output=True, text=True, timeout=10,
        )
        if ps.stdout.strip() == "healthy":
            healthy = True
            break

    yield container_name, healthy

    # Teardown
    subprocess.run(
        ["docker", "rm", "-f", container_name],
        capture_output=True,
    )
    subprocess.run(
        ["docker", "volume", "rm", "-f", f"{container_name}-data"],
        capture_output=True,
    )


class TestDockerBuildAndRun:
    """Smoke tests that run inside the container or against its API."""

    def test_container_healthy(self, run_container):
        _, healthy = run_container
        assert healthy, "Container did not become healthy within 60s"

    def test_health_endpoint(self, run_container):
        name, healthy = run_container
        if not healthy:
            pytest.skip("Container not healthy")
        result = subprocess.run(
            ["docker", "exec", name, "python", "-c",
             "import urllib.request; r = urllib.request.urlopen('http://localhost:8080/api/health'); print(r.read().decode())"],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0, f"Health check failed:\n{result.stderr}"
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert "version" in data

    def test_index_served(self, run_container):
        name, healthy = run_container
        if not healthy:
            pytest.skip("Container not healthy")
        result = subprocess.run(
            ["docker", "exec", name, "python", "-c",
             "import urllib.request; r = urllib.request.urlopen('http://localhost:8080/'); print(r.status, r.headers.get('content-type', ''))"],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0
        assert "200" in result.stdout
        assert "text/html" in result.stdout

    def test_container_version_label(self, run_container):
        name, _ = run_container
        result = subprocess.run(
            ["docker", "inspect", name, "--format", "{{.Config.Labels}}"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "HiveOS" in result.stdout

    def test_non_root_user(self, run_container):
        name, _ = run_container
        result = subprocess.run(
            ["docker", "exec", name, "whoami"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "hiveos"

    def test_data_dir_writable(self, run_container):
        name, _ = run_container
        result = subprocess.run(
            ["docker", "exec", name, "sh", "-c", "touch /data/.test-write && ls -la /data/.test-write && rm /data/.test-write"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, f"Data dir not writable:\n{result.stderr}"

    def test_api_domains(self, run_container):
        name, healthy = run_container
        if not healthy:
            pytest.skip("Container not healthy")
        result = subprocess.run(
            ["docker", "exec", name, "python", "-c",
             "import urllib.request; r = urllib.request.urlopen('http://localhost:8080/api/domains'); print(r.read().decode()[:500])"],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "domains" in data
