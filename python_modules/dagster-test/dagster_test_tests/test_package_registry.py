"""Test to ensure all Python packages in the repository are documented in python_packages.md."""

import re
from pathlib import Path

import pytest


def get_repo_root() -> Path:
    """Get the repository root directory."""
    current_dir = Path(__file__).resolve()
    # Navigate up from dagster-test/dagster_test_tests/ to repo root
    return current_dir.parent.parent.parent.parent


def parse_python_packages_md() -> dict[str, str]:
    """Parse .claude/python_packages.md and extract package name to path mappings."""
    repo_root = get_repo_root()
    packages_file = repo_root / ".claude" / "python_packages.md"

    if not packages_file.exists():
        pytest.fail(f"python_packages.md not found at {packages_file}")

    packages = {}
    content = packages_file.read_text()

    # Pattern to match: **package-name**: `path/to/package`
    pattern = r"\*\*([^*]+)\*\*:\s*`([^`]+)`"

    for match in re.finditer(pattern, content):
        package_name = match.group(1).strip()
        package_path = match.group(2).strip()
        # Convert relative path to absolute path for comparison
        absolute_path = str(repo_root / package_path)
        packages[package_name] = absolute_path

    return packages


def find_actual_packages() -> dict[str, str]:
    """Find all Python packages in the repository by looking for setup.py files."""
    repo_root = get_repo_root()
    python_modules_dir = repo_root / "python_modules"

    if not python_modules_dir.exists():
        pytest.fail(f"python_modules directory not found at {python_modules_dir}")

    packages = {}

    # Find all setup.py files in python_modules
    for setup_file in python_modules_dir.rglob("setup.py"):
        package_dir = setup_file.parent

        # Get absolute path
        abs_path = str(package_dir)

        # Extract package name from directory name
        package_name = package_dir.name

        # Skip if this is a nested test package, build artifact, or internal package
        skip_patterns = {
            "_tests",
            "build",
            "kitchen-sink",
            "__pycache__",
            ".tox",
            ".pytest_cache",
            "dist",
            ".git",
        }

        # Skip CI-specific build artifacts that appear in CI but not locally
        ci_build_artifacts = {"cython", "limited_api", "plugin"}

        if any(
            part.endswith("_tests") or part in skip_patterns or part in ci_build_artifacts
            for part in package_dir.parts
        ):
            continue

        packages[package_name] = abs_path

    return packages


def test_python_packages_md_completeness():
    """Test that all Python packages in the repository are documented in python_packages.md."""
    documented_packages = parse_python_packages_md()
    actual_packages = find_actual_packages()

    # Find packages that exist but aren't documented
    missing_from_docs = set(actual_packages.keys()) - set(documented_packages.keys())

    # Find packages that are documented but don't exist
    extra_in_docs = set(documented_packages.keys()) - set(actual_packages.keys())

    # Build error messages
    errors = []

    if missing_from_docs:
        errors.append(f"Packages missing from python_packages.md: {sorted(missing_from_docs)}")

    if extra_in_docs:
        errors.append(
            f"Packages in python_packages.md but not found in repository: {sorted(extra_in_docs)}"
        )

    # Check path accuracy for packages that exist in both
    path_mismatches = []
    for package in set(documented_packages.keys()) & set(actual_packages.keys()):
        documented_path = documented_packages[package]
        actual_path = actual_packages[package]
        if documented_path != actual_path:
            path_mismatches.append(
                f"{package}: documented='{documented_path}' actual='{actual_path}'"
            )

    if path_mismatches:
        errors.append(f"Path mismatches in python_packages.md: {path_mismatches}")

    if errors:
        pytest.fail("\n".join(errors))


def test_python_packages_md_format():
    """Test that python_packages.md follows the expected format."""
    repo_root = get_repo_root()
    packages_file = repo_root / ".claude" / "python_packages.md"

    if not packages_file.exists():
        pytest.fail(f"python_packages.md not found at {packages_file}")

    content = packages_file.read_text()

    # Check that file starts with expected header
    assert content.startswith("# python package locations"), (
        "File should start with '# python package locations'"
    )

    # Check that all package entries follow the expected format
    package_pattern = r"\*\*([^*]+)\*\*:\s*`([^`]+)`"
    matches = list(re.finditer(package_pattern, content))

    assert len(matches) > 0, "No package entries found in expected format"

    # Verify all paths are relative and point to python_modules
    for match in matches:
        package_name = match.group(1)
        package_path = match.group(2)

        assert not package_path.startswith("/"), (
            f"Path for {package_name} should be relative, not absolute: {package_path}"
        )
        assert "python_modules" in package_path, (
            f"Path for {package_name} should contain 'python_modules': {package_path}"
        )


def test_python_packages_md_exists():
    """Test that the python_packages.md file exists in the expected location."""
    repo_root = get_repo_root()
    packages_file = repo_root / ".claude" / "python_packages.md"

    assert packages_file.exists(), f"python_packages.md should exist at {packages_file}"
    assert packages_file.is_file(), f"{packages_file} should be a file"

    # Check that file is not empty
    content = packages_file.read_text()
    assert len(content.strip()) > 0, "python_packages.md should not be empty"


if __name__ == "__main__":
    # Allow running this test directly for debugging
    test_python_packages_md_exists()
    test_python_packages_md_format()
    test_python_packages_md_completeness()
