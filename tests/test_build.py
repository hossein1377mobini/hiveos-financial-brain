"""
Tests for the PyInstaller build system.

Validates version detection, data collection, and build configuration.
"""

import sys
import os
from pathlib import Path

import pytest

# Add build/ to path so we can import build_exe
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = PROJECT_ROOT / "build"
sys.path.insert(0, str(BUILD_DIR))

import build_exe


class TestVersion:
    """Version detection from pyproject.toml."""

    def test_returns_string(self):
        version = build_exe.get_version()
        assert isinstance(version, str)

    def test_matches_pyproject(self):
        """Version should match pyproject.toml."""
        import tomllib
        pyproject = PROJECT_ROOT / "pyproject.toml"
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        expected = data["project"]["version"]
        assert build_exe.get_version() == expected

    def test_semver_format(self):
        version = build_exe.get_version()
        parts = version.split(".")
        assert len(parts) >= 2, f"Version '{version}' doesn't look like semver"
        for part in parts:
            assert part.isdigit(), f"Version part '{part}' is not numeric"


class TestPyInstallerDetection:
    """PyInstaller executable detection."""

    def test_returns_string(self):
        result = build_exe.find_pyinstaller()
        assert isinstance(result, str)

    def test_contains_pyinstaller(self):
        result = build_exe.find_pyinstaller()
        assert "pyinstaller" in result.lower() or "PyInstaller" in result


class TestDataCollection:
    """Data file collection for bundling."""

    def test_datas_returns_list(self):
        datas = build_exe.collect_datas()
        assert isinstance(datas, list)

    def test_dashboard_datas_present(self):
        """Dashboard templates/static should be collected."""
        datas = build_exe.collect_datas()
        paths = [dst for _, dst in datas]
        assert any("dashboard" in p for p in paths), \
            f"No dashboard data found in: {paths}"

    def test_all_source_dirs_exist(self):
        """All source paths in datas should exist on disk."""
        datas = build_exe.collect_datas()
        for src, _ in datas:
            assert Path(src).exists(), f"Source path does not exist: {src}"


class TestHiddenImports:
    """Hidden import collection."""

    def test_returns_list(self):
        imports = build_exe.collect_hidden_imports()
        assert isinstance(imports, list)
        assert len(imports) > 50, "Expected 50+ hidden imports"

    def test_core_modules_present(self):
        imports = build_exe.collect_hidden_imports()
        required = [
            "hiveos",
            "hiveos.cli.main",
            "hiveos.desktop.app",
            "hiveos.dashboard.server",
            "uvicorn",
            "fastapi",
            "websockets",
        ]
        for mod in required:
            assert mod in imports, f"Missing hidden import: {mod}"

    def test_no_duplicates(self):
        imports = build_exe.collect_hidden_imports()
        assert len(imports) == len(set(imports)), "Duplicate hidden imports found"


class TestBuildScript:
    """Build script configuration."""

    def test_project_root_correct(self):
        assert build_exe.PROJECT_ROOT.exists()
        assert (build_exe.PROJECT_ROOT / "pyproject.toml").exists()

    def test_icon_exists(self):
        icon = build_exe.PROJECT_ROOT / "build" / "hiveos.ico"
        assert icon.exists(), "Icon file missing"

    def test_entry_point_exists(self):
        entry = build_exe.PROJECT_ROOT / "src" / "hiveos" / "desktop" / "app.py"
        assert entry.exists(), "Desktop app entry point missing"


class TestInstallerConfig:
    """Inno Setup installer configuration."""

    def test_iss_file_exists(self):
        iss = PROJECT_ROOT / "build" / "installer.iss"
        assert iss.exists()

    def test_version_matches_pyproject(self):
        """Installer version should match pyproject.toml."""
        import tomllib
        pyproject = PROJECT_ROOT / "pyproject.toml"
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        expected = data["project"]["version"]

        iss = PROJECT_ROOT / "build" / "installer.iss"
        content = iss.read_text()
        # Inno Setup uses #define MyAppVersion "x.y.z"
        import re
        m = re.search(r'#define\s+MyAppVersion\s+"([^"]+)"', content)
        assert m, "MyAppVersion not found in installer.iss"
        assert m.group(1) == expected, \
            f"Installer version {m.group(1)} != pyproject version {expected}"
