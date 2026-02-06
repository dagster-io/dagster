"""Tests for scripts/build_and_publish.sh functionality.

These tests run the actual build_and_publish.sh script against a mock environment
to verify the sed-based transformations for version updates and dependency pin replacements.
"""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parents[3] / "scripts" / "build_and_publish.sh"


@pytest.fixture
def mock_env(tmp_path: Path) -> Path:
    """Create mock environment for running build_and_publish.sh."""
    mock_bin = tmp_path / "mock_bin"
    mock_bin.mkdir()

    # Mock buildkite-agent that returns configured metadata from environment
    # Command format: buildkite-agent meta-data get <key> [--default <value>]
    # So $3 is the key name
    buildkite_mock = mock_bin / "buildkite-agent"
    buildkite_mock.write_text(
        "#!/bin/bash\n"
        'case "$3" in\n'
        '    package-to-release-path) echo "$MOCK_PACKAGE_PATH" ;;\n'
        '    version-to-release) echo "$MOCK_VERSION" ;;\n'
        "esac\n"
    )
    buildkite_mock.chmod(0o755)

    # Mock git (no-op)
    git_mock = mock_bin / "git"
    git_mock.write_text("#!/bin/bash\nexit 0\n")
    git_mock.chmod(0o755)

    # Mock python3 (no-op for build/twine operations)
    python_mock = mock_bin / "python3"
    python_mock.write_text("#!/bin/bash\nexit 0\n")
    python_mock.chmod(0o755)

    # Mock xargs (needed by the script for __version__ updates)
    xargs_mock = mock_bin / "xargs"
    xargs_mock.write_text("#!/bin/bash\nexit 0\n")
    xargs_mock.chmod(0o755)

    return mock_bin


def run_build_and_publish(
    mock_bin: Path,
    package_path: Path,
    version: str,
) -> subprocess.CompletedProcess:
    """Run build_and_publish.sh with mock environment."""
    env = os.environ.copy()
    env["PATH"] = f"{mock_bin}:{env['PATH']}"
    env["MOCK_PACKAGE_PATH"] = str(package_path)
    env["MOCK_VERSION"] = version
    env["BUILDKITE_BRANCH"] = "test-branch"
    env["PYPI_TOKEN"] = "fake-token"

    return subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(package_path.parent),
        check=False,
    )


def test_build_and_publish_pyproject_transformation(
    tmp_path: Path,
    mock_env: Path,
) -> None:
    """Script updates version and replaces all 1!0+dev pins in pyproject.toml."""
    # Set up a realistic package directory with pyproject.toml
    package_dir = tmp_path / "dagster-foo"
    package_dir.mkdir()

    pyproject = package_dir / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "dagster-foo"\n'
        'version = "1!0+dev"\n'
        'description = "A test package"\n'
        "dependencies = [\n"
        '    "dagster==1!0+dev",\n'
        '    "dagster-pipes==1!0+dev",\n'
        '    "requests>=2.28.0",\n'
        '    "pydantic>=2.0",\n'
        "]\n"
        "\n"
        "[project.optional-dependencies]\n"
        'webserver = ["dagster-webserver[notebook]==1!0+dev"]\n'
        'test = ["pytest>=7.0"]\n',
        encoding="utf-8",
    )

    # Run the script
    result = run_build_and_publish(mock_env, package_dir, "1.9.3")

    # Script should succeed
    assert result.returncode == 0, (
        f"Script failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )

    # Verify transformations
    content = pyproject.read_text(encoding="utf-8")

    # Version field updated
    assert 'version = "1.9.3"' in content

    # All dagster dependencies pinned to release version
    assert "dagster==1.9.3" in content
    assert "dagster-pipes==1.9.3" in content
    assert "dagster-webserver[notebook]==1.9.3" in content

    # Non-dagster dependencies preserved
    assert "requests>=2.28.0" in content
    assert "pydantic>=2.0" in content
    assert "pytest>=7.0" in content

    # Package metadata preserved
    assert 'name = "dagster-foo"' in content
    assert 'description = "A test package"' in content

    # No dev versions remain
    assert "1!0+dev" not in content


def test_build_and_publish_rc_version(
    tmp_path: Path,
    mock_env: Path,
) -> None:
    """Script correctly handles release candidate versions."""
    package_dir = tmp_path / "dagster-bar"
    package_dir.mkdir()

    pyproject = package_dir / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "dagster-bar"\n'
        'version = "1!0+dev"\n'
        "dependencies = [\n"
        '    "dagster==1!0+dev",\n'
        "]\n",
        encoding="utf-8",
    )

    result = run_build_and_publish(mock_env, package_dir, "1.9.3rc1")

    assert result.returncode == 0, (
        f"Script failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )

    content = pyproject.read_text(encoding="utf-8")
    assert 'version = "1.9.3rc1"' in content
    assert "dagster==1.9.3rc1" in content
    assert "1!0+dev" not in content
