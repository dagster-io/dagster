"""Tests for public_packages module."""

import tempfile
from pathlib import Path

import pytest
from automation.dagster_docs.public_packages import (
    PublicPackage,
    get_public_dagster_packages,
    get_public_module_names,
    get_public_package_names,
    get_top_level_modules,
    get_top_level_packages,
    is_public_dagster_module,
    is_public_dagster_package,
)


class TestPublicPackages:
    """Test suite for public package discovery functions."""

    def test_get_public_dagster_packages_with_real_repo(self):
        """Test getting public packages from the real Dagster repository."""
        packages = get_public_dagster_packages()

        # Should have at least the core dagster package
        assert len(packages) > 0

        # Should include dagster core
        dagster_core = next((p for p in packages if p.name == "dagster"), None)
        assert dagster_core is not None
        assert dagster_core.module_name == "dagster"
        assert dagster_core.directory_name == "dagster"

        # Should include dagster-pipes
        dagster_pipes = next((p for p in packages if p.name == "dagster-pipes"), None)
        assert dagster_pipes is not None
        assert dagster_pipes.module_name == "dagster_pipes"
        assert dagster_pipes.directory_name == "dagster-pipes"

        # Should include libraries from the libraries/ directory (the repo should have many)
        library_packages = [p for p in packages if p.name not in ["dagster", "dagster-pipes"]]
        assert len(library_packages) > 10  # Should have many library packages

        # All library packages should start with "dagster-"
        for lib in library_packages:
            assert lib.name.startswith("dagster-")
            assert lib.module_name == lib.name.replace("-", "_")

        # All packages should have proper module name conversion
        for pkg in packages:
            assert pkg.module_name == pkg.name.replace("-", "_")

        # Packages should be sorted by name
        package_names = [p.name for p in packages]
        assert package_names == sorted(package_names)

        # All packages should have valid paths that exist
        for pkg in packages:
            assert pkg.path.exists()
            assert pkg.path.is_dir()

    def test_get_public_dagster_packages_with_mock_structure(self):
        """Test getting public packages from a mock directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create mock directory structure
            python_modules_dir = temp_path / "python_modules"
            python_modules_dir.mkdir()

            # Create dagster core package
            dagster_dir = python_modules_dir / "dagster"
            dagster_dir.mkdir()
            (dagster_dir / "setup.py").write_text("# dagster setup")

            # Create dagster-pipes package
            pipes_dir = python_modules_dir / "dagster-pipes"
            pipes_dir.mkdir()
            (pipes_dir / "setup.py").write_text("# dagster-pipes setup")

            packages = get_public_dagster_packages(temp_path)

            assert len(packages) == 2  # dagster + dagster-pipes

            # Check dagster core
            dagster_pkg = next(p for p in packages if p.name == "dagster")
            assert dagster_pkg.module_name == "dagster"

            # Check dagster-pipes
            pipes_pkg = next(p for p in packages if p.name == "dagster-pipes")
            assert pipes_pkg.module_name == "dagster_pipes"

            # Check module name conversion
            for pkg in packages:
                assert pkg.module_name == pkg.name.replace("-", "_")

    def test_get_public_dagster_packages_missing_directory(self):
        """Test error handling when python_modules directory doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with pytest.raises(FileNotFoundError, match="python_modules directory not found"):
                get_public_dagster_packages(temp_path)

    def test_get_public_dagster_packages_no_core_package(self):
        """Test behavior when dagster core package is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create python_modules but no dagster core
            python_modules_dir = temp_path / "python_modules"
            python_modules_dir.mkdir()

            # Create dagster-pipes but not dagster
            pipes_dir = python_modules_dir / "dagster-pipes"
            pipes_dir.mkdir()
            (pipes_dir / "setup.py").write_text("# dagster-pipes setup")

            packages = get_public_dagster_packages(temp_path)

            # Should only have the pipes package
            assert len(packages) == 1
            assert packages[0].name == "dagster-pipes"

    def test_get_public_dagster_packages_only_core(self):
        """Test behavior when only dagster core package exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create python_modules with only dagster core
            python_modules_dir = temp_path / "python_modules"
            python_modules_dir.mkdir()

            dagster_dir = python_modules_dir / "dagster"
            dagster_dir.mkdir()
            (dagster_dir / "setup.py").write_text("# dagster setup")

            packages = get_public_dagster_packages(temp_path)

            # Should only have dagster core
            assert len(packages) == 1
            assert packages[0].name == "dagster"

    def test_get_top_level_packages(self):
        """Test getting just top-level package names (dagster and dagster-pipes only)."""
        names = get_top_level_packages()

        assert "dagster" in names
        assert "dagster-pipes" in names
        assert all(isinstance(name, str) for name in names)

        # Should be sorted
        assert names == sorted(names)

        # Should only contain the two top-level packages
        assert len(names) == 2
        assert set(names) == {"dagster", "dagster-pipes"}

    def test_get_top_level_modules(self):
        """Test getting just top-level module names (dagster and dagster_pipes only)."""
        module_names = get_top_level_modules()

        assert "dagster" in module_names
        assert "dagster_pipes" in module_names
        assert all(isinstance(name, str) for name in module_names)

        # Should be sorted
        assert module_names == sorted(module_names)

        # Should not contain dashes (converted to underscores)
        assert all("-" not in name for name in module_names)

        # Should only contain the two top-level modules
        assert len(module_names) == 2
        assert set(module_names) == {"dagster", "dagster_pipes"}

    def test_get_public_package_names(self):
        """Test getting all public package names (top-level packages + libraries)."""
        names = get_public_package_names()

        # Should include top-level packages
        assert "dagster" in names
        assert "dagster-pipes" in names

        # Should include many libraries
        library_names = [name for name in names if name not in ["dagster", "dagster-pipes"]]
        assert len(library_names) > 10

        # All library names should start with "dagster-"
        for lib_name in library_names:
            assert lib_name.startswith("dagster-")

        # Should be sorted
        assert names == sorted(names)

    def test_get_public_module_names(self):
        """Test getting all public module names (top-level packages + libraries)."""
        module_names = get_public_module_names()

        # Should include top-level modules
        assert "dagster" in module_names
        assert "dagster_pipes" in module_names

        # Should include many library modules
        library_modules = [
            name for name in module_names if name not in ["dagster", "dagster_pipes"]
        ]
        assert len(library_modules) > 10

        # All library modules should start with "dagster_"
        for lib_module in library_modules:
            assert lib_module.startswith("dagster_")

        # Should not contain dashes (converted to underscores)
        assert all("-" not in name for name in module_names)

        # Should be sorted
        assert module_names == sorted(module_names)

    def test_is_public_dagster_package(self):
        """Test checking if a package name is public."""
        assert is_public_dagster_package("dagster") is True
        assert is_public_dagster_package("dagster-pipes") is True
        assert is_public_dagster_package("not-dagster") is False
        assert is_public_dagster_package("") is False

    def test_is_public_dagster_module(self):
        """Test checking if a module name is public."""
        assert is_public_dagster_module("dagster") is True
        assert is_public_dagster_module("dagster_pipes") is True
        assert is_public_dagster_module("not_dagster") is False
        assert is_public_dagster_module("") is False

    def test_public_package_record(self):
        """Test the PublicPackage record structure."""
        pkg = PublicPackage(
            name="dagster-test",
            directory_name="dagster-test",
            module_name="dagster_test",
            path=Path("/fake/path"),
        )

        assert pkg.name == "dagster-test"
        assert pkg.directory_name == "dagster-test"
        assert pkg.module_name == "dagster_test"
        assert pkg.path == Path("/fake/path")

        # Test record immutability
        with pytest.raises(AttributeError):
            pkg.name = "changed"  # type: ignore

    def test_package_name_to_module_name_conversion(self):
        """Test that package names are correctly converted to module names."""
        packages = get_public_dagster_packages()

        for pkg in packages:
            assert pkg.module_name == pkg.name.replace("-", "_")
            if pkg.name != "dagster":
                assert pkg.name.startswith("dagster-")
                assert pkg.module_name.startswith("dagster_")

    def test_consistent_ordering(self):
        """Test that functions return consistent ordering across calls."""
        packages1 = get_public_dagster_packages()
        packages2 = get_public_dagster_packages()
        assert [p.name for p in packages1] == [p.name for p in packages2]

        # Test top-level functions
        top_level_packages1 = get_top_level_packages()
        top_level_packages2 = get_top_level_packages()
        assert top_level_packages1 == top_level_packages2

        top_level_modules1 = get_top_level_modules()
        top_level_modules2 = get_top_level_modules()
        assert top_level_modules1 == top_level_modules2

        # Test all public functions
        public_names1 = get_public_package_names()
        public_names2 = get_public_package_names()
        assert public_names1 == public_names2

        public_modules1 = get_public_module_names()
        public_modules2 = get_public_module_names()
        assert public_modules1 == public_modules2
