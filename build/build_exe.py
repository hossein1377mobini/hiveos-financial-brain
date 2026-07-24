"""
HiveOS PyInstaller Build Script — bundles the desktop app into a single .exe.

Usage (from project root):
    .venv/Scripts/python.exe build/build_exe.py

Or use the CLI:
    hive build exe

Output: dist/HiveOS.exe (--onefile) or dist/HiveOS/ (--onedir)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tomllib
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build" / "pyinstaller"
SPEC_DIR = PROJECT_ROOT / "build"

# ── Version ──────────────────────────────────────────────────────────

def get_version() -> str:
    """Read version from pyproject.toml."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if pyproject.exists():
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        return data.get("project", {}).get("version", "0.0.0")
    # Fallback: read __init__.py
    init = PROJECT_ROOT / "src" / "hiveos" / "__init__.py"
    if init.exists():
        for line in init.read_text().splitlines():
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.0.0"


# ── PyInstaller detection ────────────────────────────────────────────

def find_pyinstaller() -> str:
    """Find pyinstaller executable, preferring venv."""
    # 1. Check if pyinstaller is in PATH (works if venv is activated)
    which = shutil.which("pyinstaller")
    if which:
        return which

    # 2. Check project venv
    venv_pyinstaller = PROJECT_ROOT / ".venv" / "Scripts" / "pyinstaller.exe"
    if venv_pyinstaller.exists():
        return str(venv_pyinstaller)

    # 3. Check for python -m PyInstaller
    python = sys.executable
    try:
        result = subprocess.run(
            [python, "-m", "PyInstaller", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return f"{python} -m PyInstaller"
    except Exception:
        pass

    print("❌ PyInstaller not found.", file=sys.stderr)
    print("   Install: .venv/Scripts/pip.exe install pyinstaller", file=sys.stderr)
    sys.exit(1)


# ── Clean ────────────────────────────────────────────────────────────

def clean():
    """Remove previous build artifacts."""
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
    print("🧹 Cleaned build artifacts.")


# ── Data collection ──────────────────────────────────────────────────

def collect_datas() -> list[str]:
    """Collect all data files that need to be bundled."""
    datas = []

    # Dashboard templates and static files
    dashboard_dir = PROJECT_ROOT / "src" / "hiveos" / "dashboard"
    for subdir in ["templates", "static"]:
        src = dashboard_dir / subdir
        if src.exists():
            datas.append((str(src), f"hiveos/dashboard/{subdir}"))

    # Domains directory
    domains_dir = PROJECT_ROOT / "domains"
    if domains_dir.exists():
        datas.append((str(domains_dir), "domains"))

    # Prototype flows
    prototype_dir = PROJECT_ROOT / "prototype"
    if prototype_dir.exists():
        datas.append((str(prototype_dir), "prototype"))

    return datas


def collect_hidden_imports() -> list[str]:
    """Collect all hidden imports for PyInstaller."""
    imports = [
        # Core
        "hiveos",
        "hiveos.cli.main",
        "hiveos.cli.build",
        # Desktop
        "hiveos.desktop",
        "hiveos.desktop.app",
        # Dashboard
        "hiveos.dashboard",
        "hiveos.dashboard.server",
        "hiveos.dashboard.app",
        "hiveos.dashboard.auth",
        "hiveos.dashboard.config_service",
        "hiveos.dashboard.routes",
        "hiveos.dashboard.routes.config",
        "hiveos.dashboard.routes.deps",
        "hiveos.dashboard.routes.domain_packs",
        "hiveos.dashboard.routes.history",
        "hiveos.dashboard.routes.knowledge",
        "hiveos.dashboard.routes.skills",
        "hiveos.dashboard.routes.workflows",
        # Playground
        "hiveos.playground",
        "hiveos.playground.playground",
        "hiveos.playground.runner",
        "hiveos.playground.library",
        # Brain
        "hiveos.brain",
        "hiveos.brain.approval_gate",
        "hiveos.brain.decision_tracer",
        "hiveos.brain.event_stream",
        # Learning
        "hiveos.learning",
        "hiveos.learning.analytics",
        # Storage
        "hiveos.storage",
        "hiveos.storage.engine",
        # Domain
        "hiveos.domain",
        "hiveos.domain.manager",
        "hiveos.domain.registry",
        "hiveos.domain_pack",
        "hiveos.domain_pack.manager",
        "hiveos.domain_pack.models",
        "hiveos.domain_pack.registry",
        "hiveos.domain_pack.validator",
        "hiveos.domain_pack.loader",
        # Knowledge
        "hiveos.knowledge",
        "hiveos.knowledge.service",
        "hiveos.knowledge.indexing",
        "hiveos.knowledge.search",
        "hiveos.knowledge.ingestion",
        # Audit
        "hiveos.audit",
        "hiveos.audit.trail",
        "hiveos.audit.models",
        # RBAC
        "hiveos.rbac",
        # Update
        "hiveos.update",
        # Package
        "hiveos.package",
        "hiveos.registry",
        # Mothership
        "hiveos.mothership",
        "hiveos.mothership.communication_bus",
        "hiveos.mothership.task_router",
        # Sync
        "hiveos.sync",
        # Utils
        "hiveos.utils.config",
        "hiveos.utils.validator",
        "hiveos.utils.knowledge",
        # uvicorn
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        # websockets
        "websockets",
        "websockets.legacy",
        "websockets.legacy.client",
        # Pydantic
        "pydantic",
        "pydantic_core",
        # FastAPI
        "fastapi",
        "fastapi.responses",
        "fastapi.staticfiles",
        "fastapi.templating",
        # Click
        "click",
        "click.core",
        "click.types",
        # Rich
        "rich",
        "rich.console",
        "rich.panel",
        "rich.table",
        # YAML
        "yaml",
    ]
    return imports


# ── Build ────────────────────────────────────────────────────────────

def build_exe(
    onefile: bool = True,
    console: bool = False,
    ci_mode: bool = False,
):
    """Run PyInstaller to produce HiveOS.exe.

    Args:
        onefile: If True, produce single .exe; if False, produce folder.
        console: If True, show console window (for debugging).
        ci_mode: If True, skip --windowed flag (CI has no display).
    """
    pyinstaller_cmd = find_pyinstaller()
    version = get_version()
    icon_path = PROJECT_ROOT / "build" / "hiveos.ico"
    entry_point = str(PROJECT_ROOT / "src" / "hiveos" / "desktop" / "app.py")

    # Build data args
    datas = collect_datas()
    data_args = []
    for src, dst in datas:
        if Path(src).exists():
            sep = ";" if sys.platform == "win32" else ":"
            data_args.append(f"--add-data={src}{sep}{dst}")

    # Hidden imports
    hidden_imports = collect_hidden_imports()
    hi_args = [f"--hidden-import={imp}" for imp in hidden_imports]

    # Build command
    cmd_parts = pyinstaller_cmd.split()
    cmd = cmd_parts + [
        "--noconfirm",
        "--clean",
        f"--name=HiveOS",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        f"--specpath={SPEC_DIR}",
        "--exclude-module=pythoncom",
        "--exclude-module=pywin32",
        "--collect-all=hiveos",
    ]

    # Onefile vs onedir
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    # Windowed mode (no console)
    if not console and not ci_mode:
        cmd.append("--windowed")

    # Icon
    if icon_path.exists():
        cmd.append(f"--icon={icon_path}")

    # Add data and hidden imports
    cmd.extend(data_args)
    cmd.extend(hi_args)

    # Entry point
    cmd.append(entry_point)

    print(f"🚀 Building HiveOS v{version} ...")
    if onefile:
        print("   Mode: --onefile (single .exe)")
    else:
        print("   Mode: --onedir (folder)")
    print(f"   Datas: {len(datas)} entries")
    print(f"   Hidden imports: {len(hidden_imports)} entries")
    print()

    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ PyInstaller failed:", file=sys.stderr)
        # Show last part of output
        stdout = result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout
        stderr = result.stderr[-3000:] if len(result.stderr) > 3000 else result.stderr
        if stdout:
            print(stdout, file=sys.stderr)
        if stderr:
            print(stderr, file=sys.stderr)
        sys.exit(result.returncode)

    print()
    print("✅ Build complete!")

    if onefile:
        exe_path = DIST_DIR / "HiveOS.exe"
    else:
        exe_path = DIST_DIR / "HiveOS" / "HiveOS.exe"

    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"   📦 {exe_path}")
        print(f"   📏 Size: {size_mb:.1f} MB")
        print()
        print("   Next steps:")
        print(f"     1. Test: {exe_path}")
        print("     2. If Inno Setup installed: iscc build\\installer.iss")
        print(f"     3. Or distribute {exe_path.name} directly")
    else:
        print(f"   ⚠ Expected output not found at {exe_path}")
        # Check what was produced
        for f in DIST_DIR.rglob("*.exe"):
            print(f"   Found: {f}")

    return str(exe_path) if exe_path.exists() else None


# ── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build HiveOS executable")
    parser.add_argument(
        "--onedir", action="store_true",
        help="Produce a folder instead of single .exe",
    )
    parser.add_argument(
        "--console", action="store_true",
        help="Keep console window (for debugging)",
    )
    parser.add_argument(
        "--ci", action="store_true",
        help="CI mode: skip --windowed flag",
    )
    parser.add_argument(
        "--no-clean", action="store_true",
        help="Skip cleaning previous build artifacts",
    )
    args = parser.parse_args()

    if not args.no_clean:
        clean()

    build_exe(
        onefile=not args.onedir,
        console=args.console,
        ci_mode=args.ci,
    )


if __name__ == "__main__":
    main()
