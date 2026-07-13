"""
CLI package build command helpers.
"""

from pathlib import Path
from rich.console import Console
from ..package import PackageBuilder

console = Console()


def build_package(source_dir: Path, output: Path) -> Path:
    """Build a HiveOS package from a source directory."""
    builder = PackageBuilder(source_dir)
    return builder.build(output)


def create_manifest(pkg_dir: Path, name: str, description: str,
                    author: str, version: str = "0.1.0") -> Path:
    """Create a manifest.yaml in a package directory."""
    import yaml
    manifest = {
        "name": name,
        "version": version,
        "description": description,
        "author": author,
        "dependencies": [],
        "flows": [],
        "requires_hiveos_version": ">=0.1.0",
    }
    manifest_path = pkg_dir / "manifest.yaml"
    with open(manifest_path, "w", encoding="utf-8") as f:
        yaml.dump(manifest, f, default_flow_style=False, allow_unicode=True)
    console.print(f"✅ Created manifest: {manifest_path}")
    return manifest_path
