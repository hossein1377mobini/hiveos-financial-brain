"""
HiveOS PyInstaller Build Script — bundles the desktop app into a single .exe.

Phase C of the Windows Native roadmap:
  PyInstaller → single backend.exe so users don't need Python installed.

Usage:
    uv pip install pyinstaller
    python build/build_exe.py

Output: dist/HiveOS.exe
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build" / "pyinstaller"

# Files and dirs to include alongside the .exe
DOMAINS_DIR = PROJECT_ROOT / "domains"
ADDITIONAL_DATA = [
    (str(DOMAINS_DIR), "domains"),
]


def clean():
    """Remove previous build artifacts."""
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
    print("🧹 Cleaned build artifacts.")


def build_exe():
    """Run PyInstaller to produce HiveOS.exe."""
    if not shutil.which("pyinstaller"):
        print(
            "❌ PyInstaller not found. Install with: uv pip install pyinstaller",
            file=sys.stderr,
        )
        sys.exit(1)

    entry_point = str(PROJECT_ROOT / "src" / "hiveos" / "desktop" / "app.py")
    icon_path = str(PROJECT_ROOT / "build" / "hiveos.ico")

    # Build the dataspec for --add-data
    data_args = []
    for src, dst in ADDITIONAL_DATA:
        if Path(src).exists():
            data_args.append(f"--add-data={src}{os.pathsep}{dst}")

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--onedir",  # Faster startup than --onefile, better for debug
        "--name=HiveOS",
        "--distpath=" + str(DIST_DIR),
        "--workpath=" + str(BUILD_DIR),
        "--specpath=" + str(PROJECT_ROOT / "build"),
        "--hidden-import=hiveos",
        "--hidden-import=hiveos.cli.main",
        "--hidden-import=hiveos.desktop",
        "--hidden-import=hiveos.desktop.app",
        "--hidden-import=hiveos.dashboard",
        "--hidden-import=hiveos.dashboard.server",
        "--hidden-import=hiveos.playground",
        "--hidden-import=hiveos.playground.playground",
        "--hidden-import=hiveos.playground.runner",
        "--hidden-import=hiveos.playground.library",
        "--hidden-import=hiveos.brain",
        "--hidden-import=hiveos.learning",
        "--hidden-import=hiveos.storage",
        "--hidden-import=hiveos.domain",
        "--hidden-import=hiveos.update",
        "--hidden-import=uvicorn",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=websockets",
        "--collect-all=hiveos",
        "--windowed",  # No console window for end users
    ]

    if Path(icon_path).exists():
        cmd.append(f"--icon={icon_path}")

    cmd.extend(data_args)
    cmd.append(entry_point)

    print("🚀 Running PyInstaller...")
    print(f"   Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ PyInstaller failed:")
        print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
        print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
        sys.exit(result.returncode)

    print("✅ Build complete!")
    exe_path = DIST_DIR / "HiveOS" / "HiveOS.exe"
    if exe_path.exists():
        print(f"   📦 {exe_path}")
    return str(DIST_DIR / "HiveOS")


def make_icon():
    """Generate a minimal .ico file if none exists (placeholder)."""
    ico_path = PROJECT_ROOT / "build" / "hiveos.ico"
    if ico_path.exists():
        return

    # Use Python to create a minimal valid .ico (32x32, 1-bit)
    # This is a fallback — users should replace with a real icon.
    try:
        import struct
        from io import BytesIO

        # Minimal 32x32 1-bpp BMP
        width, height = 32, 32
        pixels = b"\xff" * (width * height // 8)  # all white
        xor_mask = pixels
        and_mask = b"\x00" * (width * height // 8)

        bmp_size = 40 + len(xor_mask) + len(and_mask)
        bmp_data = BytesIO()
        # BITMAPINFOHEADER
        bmp_data.write(struct.pack("<I", 40))  # size
        bmp_data.write(struct.pack("<i", width))
        bmp_data.write(struct.pack("<i", height * 2))  # height * 2 for ICO
        bmp_data.write(struct.pack("<H", 1))  # planes
        bmp_data.write(struct.pack("<H", 1))  # bpp
        bmp_data.write(struct.pack("<I", 0))  # compression
        bmp_data.write(struct.pack("<I", len(xor_mask) + len(and_mask)))
        bmp_data.write(struct.pack("<i", 0))  # hres
        bmp_data.write(struct.pack("<i", 0))  # vres
        bmp_data.write(struct.pack("<I", 0))  # colors
        bmp_data.write(struct.pack("<I", 0))  # important
        bmp_data.write(xor_mask)
        bmp_data.write(and_mask)

        # ICO directory entry + BMP data
        ico_data = BytesIO()
        ico_data.write(struct.pack("<H", 0))  # reserved
        ico_data.write(struct.pack("<H", 1))  # ICO type
        ico_data.write(struct.pack("<H", 1))  # 1 image
        # Directory entry
        ico_data.write(struct.pack("B", width if width < 256 else 0))
        ico_data.write(struct.pack("B", height if height < 256 else 0))
        ico_data.write(struct.pack("B", 0))  # colors
        ico_data.write(struct.pack("B", 0))  # reserved
        ico_data.write(struct.pack("<H", 1))  # planes
        ico_data.write(struct.pack("<H", 1))  # bpp
        ico_data.write(struct.pack("<I", bmp_data.tell()))  # size
        ico_data.write(struct.pack("<I", 22))  # offset (6 + 16)
        ico_data.write(bmp_data.getvalue())

        ico_path.parent.mkdir(parents=True, exist_ok=True)
        ico_path.write_bytes(ico_data.getvalue())
        print(f"📦 Generated placeholder icon: {ico_path}")
        print("   ⚠ Replace with a real .ico file for production builds.")
    except Exception as exc:
        print(f"⚠ Could not generate icon: {exc}")
        print("   A real .ico is needed for the installer. Skipping icon.")


if __name__ == "__main__":
    make_icon()
    clean()
    build_exe()
