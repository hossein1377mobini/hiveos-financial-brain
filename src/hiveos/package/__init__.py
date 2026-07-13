"""
HiveOS Package Format - build, install, and manage HiveOS packages.

A HiveOS package is a .tar.gz archive containing:
- flows/          → Flow DSL YAML files
- skills/          → Hermes skill markdown files
- knowledge/       → Knowledge base markdown files
- config/          → Package configuration
- manifest.yaml    → Package manifest metadata
"""

from pathlib import Path
import tarfile
import yaml
import json
from typing import Dict, List, Optional, Any
from rich.console import Console
from dataclasses import dataclass

console = Console()

PACKAGE_STRUCTURE = {
    "flows/": "*.yml",
    "skills/": "*.md",
    "knowledge/": "*.md",
    "config/": "*.yaml",
}

@dataclass
class Manifest:
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = None
    flows: List[str] = None
    requires_hiveos_version: str = ">=0.1.0"
    
MANIFEST_TEMPLATE = {
    "name": "",
    "version": "0.1.0",
    "description": "",
    "author": "",
    "dependencies": [],
    "flows": [],
    "requires_hiveos_version": ">=0.1.0"
}

class PackageBuilder:
    """Build HiveOS packages from source directories."""
    
    def __init__(self, source_dir: Path):
        self.source_dir = Path(source_dir)
        self.manifest_path = self.source_dir / "manifest.yaml"
    
    def build(self, output_path: Path) -> Path:
        """Build a package from source directory to .tar.gz"""
        console.print(f"📦 Building package from: {self.source_dir}")
        
        # Validate structure
        self._validate_source()
        
        # Create the archive
        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(self.source_dir, arcname="", filter=self._tar_filter)
        
        console.print(f"✅ Package built: {output_path}")
        return output_path
    
    def _validate_source(self):
        """Check source directory has the expected structure."""
        if not self.source_dir.exists():
            raise ValueError(f"Source directory does not exist: {self.source_dir}")
        
        # manifest.yaml is optional in source (generated during build if missing)
    
    def _tar_filter(self, tarinfo):
        """Filter what goes into the package archive."""
        # Skip .git and __pycache__
        if ".git" in tarinfo.name.split("/"):
            return None
        if "__pycache__" in tarinfo.name.split("/"):
            return None
        if tarinfo.name.startswith("src/"):
            return None
        if tarinfo.name.endswith(".pyc"):
            return None
        return tarinfo


class PackageInstaller:
    """Install HiveOS packages."""
    
    def __init__(self, install_dir: Optional[Path] = None):
        self.install_dir = install_dir or Path.home() / ".hiveos" / "packages"
    
    def install(self, package_path: Path) -> Manifest:
        """Install a package to the install directory."""
        console.print(f"📥 Installing package: {package_path}")
        
        self.install_dir.mkdir(parents=True, exist_ok=True)
        
        with tarfile.open(package_path, "r:gz") as tar:
            # Read manifest first
            manifest_file = None
            for member in tar.getmembers():
                if member.name == "manifest.yaml":
                    manifest_file = tar.extractfile(member)
                    break
            
            if manifest_file is None:
                raise ValueError("Package does not contain manifest.yaml")
            
            manifest_data = yaml.safe_load(manifest_file.read())
            manifest = Manifest(
                name=manifest_data.get("name", "unknown"),
                version=manifest_data.get("version", "0.0.0"),
                description=manifest_data.get("description", ""),
                author=manifest_data.get("author", ""),
                dependencies=manifest_data.get("dependencies", []),
                flows=manifest_data.get("flows", []),
                requires_hiveos_version=manifest_data.get("requires_hiveos_version", ">=0.1.0"),
            )
            
            # Extract to install directory
            package_dir = self.install_dir / f"{manifest.name}-{manifest.version}"
            if package_dir.exists():
                console.print(f"⚠️  Package {manifest.name}-{manifest.version} already installed, overwriting...")
            
            tar.extractall(path=package_dir)
        
        console.print(f"✅ Installed {manifest.name} v{manifest.version}")
        return manifest
    
    def list_packages(self) -> List[Manifest]:
        """List all installed packages."""
        if not self.install_dir.exists():
            return []
        
        packages = []
        for pkg_dir in sorted(self.install_dir.iterdir()):
            manifest_file = pkg_dir / "manifest.yaml"
            if manifest_file.exists():
                manifest_data = yaml.safe_load(manifest_file.read_text())
                if manifest_data:
                    packages.append(Manifest(
                        name=manifest_data.get("name", "unknown"),
                        version=manifest_data.get("version", "0.0.0"),
                        description=manifest_data.get("description", ""),
                        author=manifest_data.get("author", ""),
                    ))
        
        return packages
    
    def uninstall(self, package_name: str) -> bool:
        """Remove an installed package."""
        import shutil
        
        for pkg_dir in self.install_dir.iterdir():
            if pkg_dir.name.startswith(package_name):
                shutil.rmtree(pkg_dir)
                console.print(f"🗑️  Uninstalled: {package_name}")
                return True
        
        console.print(f"❌ Package not found: {package_name}")
        return False


def create_manifest_yaml(package_dir: Path, name: str, description: str, 
                         author: str, version: str = "0.1.0") -> Path:
    """Create a manifest.yaml file for a HiveOS package."""
    manifest = {
        "name": name,
        "version": version,
        "description": description,
        "author": author,
        "dependencies": [],
        "flows": [],
        "requires_hiveos_version": ">=0.1.0"
    }
    
    manifest_path = package_dir / "manifest.yaml"
    with open(manifest_path, "w", encoding="utf-8") as f:
        yaml.dump(manifest, f, default_flow_style=False, allow_unicode=True)
    
    console.print(f"✅ Created manifest: {manifest_path}")
    return manifest_path
