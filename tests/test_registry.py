"""Tests for Package Registry."""

import pytest
import tempfile
import shutil
from pathlib import Path

from hiveos.registry.registry import PackageRegistry, RegistryEntry, RegistryConfig
from hiveos.package import PackageBuilder, PackageInstaller, create_manifest_yaml


@pytest.fixture
def temp_registry():
    """Create a temporary registry for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = RegistryConfig(registry_dir=Path(tmpdir) / ".hiveos" / "registry")
        yield PackageRegistry(config)


@pytest.fixture
def sample_package_dir():
    """Create a sample package directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pkg_dir = Path(tmpdir) / "test-package"
        pkg_dir.mkdir()

        # Create structure
        (pkg_dir / "flows").mkdir()
        (pkg_dir / "skills").mkdir()
        (pkg_dir / "knowledge").mkdir()
        (pkg_dir / "config").mkdir()

        # Create a flow
        flow_file = pkg_dir / "flows" / "test-flow.yml"
        flow_file.write_text("""name: "Test Flow"
description: "A test flow"
version: "0.1.0"

trigger:
  type: manual

agents:
  - id: agent1
    name: "Agent 1"
    skills:
      - text-generation
    output: result.txt

deliver:
  to: origin
  format: markdown
""")

        # Create manifest
        create_manifest_yaml(
            pkg_dir,
            name="test-package",
            description="A test package for unit tests",
            author="Test Author",
            version="1.0.0"
        )

        yield pkg_dir


class TestRegistryEntry:
    """Test RegistryEntry dataclass."""

    def test_create_entry(self):
        entry = RegistryEntry(
            name="test-package",
            version="1.0.0",
            description="Test description",
            author="Test Author",
            tags=["tag1", "tag2"],
            dependencies=["dep1"],
            flows=["flow1.yml"],
        )
        assert entry.name == "test-package"
        assert entry.version == "1.0.0"
        assert entry.tags == ["tag1", "tag2"]

    def test_to_dict(self):
        entry = RegistryEntry(
            name="test-package",
            version="1.0.0",
            description="Test description",
            author="Test Author",
        )
        d = entry.to_dict()
        assert d["name"] == "test-package"
        assert d["version"] == "1.0.0"
        assert "published_at" in d

    def test_from_dict(self):
        data = {
            "name": "test-package",
            "version": "1.0.0",
            "description": "Test",
            "author": "Author",
            "tags": ["tag1"],
        }
        entry = RegistryEntry.from_dict(data)
        assert entry.name == "test-package"
        assert entry.tags == ["tag1"]


class TestPackageRegistry:
    """Test PackageRegistry class."""

    def test_publish_and_get(self, temp_registry):
        entry = RegistryEntry(
            name="test-package",
            version="1.0.0",
            description="Test package",
            author="Test Author",
        )
        result = temp_registry.publish(entry)
        assert result is True

        # Get the entry
        retrieved = temp_registry.get("test-package", "1.0.0")
        assert retrieved is not None
        assert retrieved.name == "test-package"
        assert retrieved.version == "1.0.0"
        assert retrieved.description == "Test package"

    def test_publish_overwrite(self, temp_registry):
        entry1 = RegistryEntry(
            name="test-package",
            version="1.0.0",
            description="Version 1",
            author="Author",
        )
        temp_registry.publish(entry1)

        # Try to publish same version without overwrite
        entry2 = RegistryEntry(
            name="test-package",
            version="1.0.0",
            description="Version 2",
            author="Author",
        )
        result = temp_registry.publish(entry2, overwrite=False)
        assert result is False  # Should fail

        # With overwrite=True
        result = temp_registry.publish(entry2, overwrite=True)
        assert result is True

        retrieved = temp_registry.get("test-package", "1.0.0")
        assert retrieved.description == "Version 2"

    def test_get_latest_version(self, temp_registry):
        for ver in ["1.0.0", "1.1.0", "2.0.0"]:
            entry = RegistryEntry(
                name="test-package",
                version=ver,
                description=f"Version {ver}",
                author="Author",
            )
            temp_registry.publish(entry)

        latest = temp_registry.get_latest_version("test-package")
        assert latest == "2.0.0"

        # Get without version should return latest
        retrieved = temp_registry.get("test-package")
        assert retrieved.version == "2.0.0"

    def test_list_packages(self, temp_registry):
        for i in range(3):
            entry = RegistryEntry(
                name=f"package-{i}",
                version="1.0.0",
                description=f"Package {i}",
                author="Author",
                tags=["tag1"] if i % 2 == 0 else ["tag2"],
            )
            temp_registry.publish(entry)

        all_packages = temp_registry.list_packages()
        assert len(all_packages) == 3

        # Filter by tag
        tag1_packages = temp_registry.list_packages(tag="tag1")
        assert len(tag1_packages) == 2
        assert all("tag1" in p.tags for p in tag1_packages)

    def test_search(self, temp_registry):
        entry = RegistryEntry(
            name="awesome-package",
            version="1.0.0",
            description="An awesome tool for testing",
            author="John Doe",
            tags=["testing", "tools"],
        )
        temp_registry.publish(entry)

        # Search by name
        results = temp_registry.search("awesome")
        assert len(results) == 1
        assert results[0].name == "awesome-package"

        # Search by description
        results = temp_registry.search("testing")
        assert len(results) == 1

        # Search by author
        results = temp_registry.search("john")
        assert len(results) == 1

        # Search by tag
        results = temp_registry.search("tools")
        assert len(results) == 1

        # No results
        results = temp_registry.search("nonexistent")
        assert len(results) == 0

    def test_remove_package(self, temp_registry):
        for ver in ["1.0.0", "2.0.0"]:
            entry = RegistryEntry(
                name="test-package",
                version=ver,
                description=f"Version {ver}",
                author="Author",
            )
            temp_registry.publish(entry)

        # Remove specific version
        temp_registry.remove("test-package", "1.0.0")
        assert temp_registry.get("test-package", "1.0.0") is None
        assert temp_registry.get("test-package", "2.0.0") is not None

        # Remove all
        temp_registry.remove("test-package")
        assert temp_registry.get("test-package") is None

    def test_increment_install(self, temp_registry):
        entry = RegistryEntry(
            name="test-package",
            version="1.0.0",
            description="Test",
            author="Author",
        )
        temp_registry.publish(entry)

        temp_registry.increment_install("test-package", "1.0.0")
        temp_registry.increment_install("test-package", "1.0.0")

        retrieved = temp_registry.get("test-package", "1.0.0")
        assert retrieved.install_count == 2

    def test_persistence(self, temp_registry):
        entry = RegistryEntry(
            name="persistent-package",
            version="1.0.0",
            description="Persistent test",
            author="Author",
        )
        temp_registry.publish(entry)

        # Create new registry with same config
        new_registry = PackageRegistry(temp_registry.config)
        retrieved = new_registry.get("persistent-package", "1.0.0")
        assert retrieved is not None
        assert retrieved.description == "Persistent test"


class TestPackageBuilder:
    """Test PackageBuilder."""

    def test_build_package(self, sample_package_dir, tmp_path):
        builder = PackageBuilder(sample_package_dir)
        output = tmp_path / "test-package.tar.gz"
        result = builder.build(output)

        assert result.exists()
        assert result.suffix == ".gz"

    def test_build_package_with_manifest(self, sample_package_dir, tmp_path):
        """Test building a package that already has manifest.yaml."""
        builder = PackageBuilder(sample_package_dir)
        output = tmp_path / "test-package-1.0.0.tar.gz"
        result = builder.build(output)

        assert result.exists()

        # Verify manifest is in the package
        import tarfile
        with tarfile.open(result, "r:gz") as tar:
            names = tar.getnames()
            assert "manifest.yaml" in names
            assert "flows/test-flow.yml" in names


class TestPackageInstaller:
    """Test PackageInstaller."""

    def test_install_package(self, sample_package_dir, tmp_path):
        # First build the package
        builder = PackageBuilder(sample_package_dir)
        pkg_path = tmp_path / "test-package-1.0.0.tar.gz"
        builder.build(pkg_path)

        # Install
        install_dir = tmp_path / "installed"
        installer = PackageInstaller(install_dir=install_dir)
        manifest = installer.install(pkg_path)

        assert manifest.name == "test-package"
        assert manifest.version == "1.0.0"
        assert manifest.description == "A test package for unit tests"

        # Check installed directory exists
        installed_pkg = install_dir / "test-package-1.0.0"
        assert installed_pkg.exists()
        assert (installed_pkg / "manifest.yaml").exists()
        assert (installed_pkg / "flows" / "test-flow.yml").exists()

    def test_list_installed(self, sample_package_dir, tmp_path):
        builder = PackageBuilder(sample_package_dir)
        pkg_path = tmp_path / "test-package-1.0.0.tar.gz"
        builder.build(pkg_path)

        install_dir = tmp_path / "installed"
        installer = PackageInstaller(install_dir=install_dir)
        installer.install(pkg_path)

        packages = installer.list_packages()
        assert len(packages) == 1
        assert packages[0].name == "test-package"

    def test_uninstall(self, sample_package_dir, tmp_path):
        builder = PackageBuilder(sample_package_dir)
        pkg_path = tmp_path / "test-package-1.0.0.tar.gz"
        builder.build(pkg_path)

        install_dir = tmp_path / "installed"
        installer = PackageInstaller(install_dir=install_dir)
        installer.install(pkg_path)

        result = installer.uninstall("test-package")
        assert result is True

        packages = installer.list_packages()
        assert len(packages) == 0

        # Try to uninstall non-existent
        result = installer.uninstall("nonexistent")
        assert result is False


class TestPackageEndToEnd:
    """End-to-end tests for package workflow."""

    def test_full_workflow_build_publish_install(self, sample_package_dir, tmp_path):
        """Test the full workflow: build -> publish -> install."""
        # 1. Build package
        builder = PackageBuilder(sample_package_dir)
        pkg_path = tmp_path / "test-package-1.0.0.tar.gz"
        builder.build(pkg_path)

        # 2. Publish to registry (with temp registry dir)
        reg_dir = tmp_path / "registry"
        config = RegistryConfig(registry_dir=reg_dir)
        reg = PackageRegistry(config)

        entry = RegistryEntry(
            name="test-package",
            version="1.0.0",
            description="A test package for unit tests",
            author="Test Author",
            tags=["test"],
            flows=["test-flow.yml"],
            source_url=str(pkg_path),
        )
        reg.publish(entry)

        # 3. Install from registry info
        install_dir = tmp_path / "installed"
        installer = PackageInstaller(install_dir=install_dir)
        manifest = installer.install(pkg_path)

        assert manifest.name == "test-package"
        assert manifest.version == "1.0.0"

        # 4. Verify install count incremented
        reg.increment_install("test-package", "1.0.0")
        entry = reg.get("test-package", "1.0.0")
        assert entry.install_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])