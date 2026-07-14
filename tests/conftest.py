"""pytest configuration for HiveOS tests."""

import pytest


@pytest.fixture(autouse=True)
def _reset_run_store():
    """Clear the global _run_store before each runner test."""
    from hiveos.playground.runner import _run_store
    _run_store.clear()
