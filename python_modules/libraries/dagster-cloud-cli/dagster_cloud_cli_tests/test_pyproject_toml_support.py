import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from dagster_cloud_cli.commands.serverless import _check_source_directory
from dagster_cloud_cli.core.pex_builder import deps, source
from dagster_cloud_cli.ui import ExitWithMessage
from packaging import version


@pytest.fixture
def temp_dir(tmp_path):
    """Pytest fixture for temporary directory."""
    return str(tmp_path)


def test_get_pyproject_toml_deps_pep_621_format(temp_dir):
    """Test parsing PEP 621 format pyproject.toml files."""
    pyproject_content = """
[project]
name = "test-package"
version = "0.1.0"
dependencies = [
    "requests>=2.25.0",
    "click>=8.0.0",
    "dagster-cloud>=1.0.0"
]

[project.optional-dependencies]
test = ["pytest>=6.0.0", "pytest-mock"]
dev = ["black", "ruff"]
"""
    pyproject_path = Path(temp_dir) / "pyproject.toml"
    pyproject_path.write_text(pyproject_content)

    deps_list = deps.get_pyproject_toml_deps(temp_dir)

    expected_deps = [
        "requests>=2.25.0",
        "click>=8.0.0",
        "dagster-cloud>=1.0.0",
        "pytest>=6.0.0",
        "pytest-mock",
        "black",
        "ruff",
    ]
    assert sorted(deps_list) == sorted(expected_deps)


def test_get_pyproject_toml_deps_poetry_format(temp_dir):
    """Test parsing Poetry format pyproject.toml files."""
    pyproject_content = """
[tool.poetry]
name = "test-package"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.9"
requests = "^2.25.0"
click = ">=8.0.0"
dagster-cloud = "^1.0.0"

[tool.poetry.dev-dependencies]
pytest = "^6.0.0"
black = "*"
"""
    pyproject_path = Path(temp_dir) / "pyproject.toml"
    pyproject_path.write_text(pyproject_content)

    deps_list = deps.get_pyproject_toml_deps(temp_dir)

    expected_deps = [
        "requests^2.25.0",
        "click>=8.0.0",
        "dagster-cloud^1.0.0",
        "pytest^6.0.0",
        "black*",
    ]
    assert sorted(deps_list) == sorted(expected_deps)


def test_get_pyproject_toml_deps_complex_poetry_format(temp_dir):
    """Test parsing Poetry format with complex dependency specs."""
    pyproject_content = """
[tool.poetry.dependencies]
python = "^3.9"
requests = {version = "^2.25.0", extras = ["security"]}
local-package = {path = "../local", develop = true}
git-package = {git = "https://github.com/user/repo.git"}
simple-dep = "^1.0.0"

[tool.poetry.dev-dependencies]
pytest = {version = "^6.0.0"}
"""
    pyproject_path = Path(temp_dir) / "pyproject.toml"
    pyproject_path.write_text(pyproject_content)

    deps_list = deps.get_pyproject_toml_deps(temp_dir)

    # Complex specs should fall back to just the package name
    expected_deps = [
        "requests^2.25.0",
        "local-package",
        "git-package",
        "simple-dep^1.0.0",
        "pytest^6.0.0",
    ]
    assert sorted(deps_list) == sorted(expected_deps)


def test_get_pyproject_toml_deps_no_file(temp_dir):
    """Test behavior when pyproject.toml doesn't exist."""
    deps_list = deps.get_pyproject_toml_deps(temp_dir)
    assert deps_list == []


def test_get_pyproject_toml_deps_invalid_toml(temp_dir):
    """Test behavior with invalid TOML content."""
    invalid_toml = """
[project
name = "invalid-toml"
"""
    pyproject_path = Path(temp_dir) / "pyproject.toml"
    pyproject_path.write_text(invalid_toml)

    with pytest.raises(ValueError, match="Error parsing pyproject.toml"):
        deps.get_pyproject_toml_deps(temp_dir)


def test_get_requirements_lines_includes_pyproject_toml(temp_dir):
    """Test that get_requirements_lines includes pyproject.toml dependencies."""
    pyproject_content = """
[project]
dependencies = ["requests>=2.25.0"]
"""
    requirements_content = "click>=8.0.0\n"

    pyproject_path = Path(temp_dir) / "pyproject.toml"
    pyproject_path.write_text(pyproject_content)

    requirements_path = Path(temp_dir) / "requirements.txt"
    requirements_path.write_text(requirements_content)

    with patch("dagster_cloud_cli.core.pex_builder.deps.get_setup_py_deps", return_value=[]):
        lines = deps.get_requirements_lines(temp_dir, "python")

        expected = ["click>=8.0.0", "requests>=2.25.0"]
        assert sorted(lines) == sorted(expected)


@patch("subprocess.run")
def test_build_local_package_with_pyproject_toml(mock_run, temp_dir):
    """Test building a package with pyproject.toml."""
    mock_run.return_value = None

    pyproject_path = Path(temp_dir) / "pyproject.toml"
    pyproject_path.write_text("""
[project]
name = "test-package"
version = "0.1.0"
""")

    build_dir = Path(temp_dir) / "build"
    build_dir.mkdir()

    source._build_local_package(temp_dir, str(build_dir), "python")  # noqa: SLF001

    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    command = args[0]

    expected_command = [
        "python",
        "-m",
        "pip",
        "install",
        "--target",
        str(build_dir),
        "--no-deps",
        ".",
    ]
    assert command == expected_command


@patch("subprocess.run")
def test_build_local_package_prefers_setup_py(mock_run, temp_dir):
    """Test that setup.py is preferred over pyproject.toml when both exist."""
    mock_run.return_value = None

    # Create both setup.py and pyproject.toml
    setup_path = Path(temp_dir) / "setup.py"
    setup_path.write_text("from setuptools import setup; setup()")

    pyproject_path = Path(temp_dir) / "pyproject.toml"
    pyproject_path.write_text("""
[project]
name = "test-package"
""")

    build_dir = Path(temp_dir) / "build"
    build_dir.mkdir()

    source._build_local_package(temp_dir, str(build_dir), "python")  # noqa: SLF001

    # Should use setup.py, not pyproject.toml
    mock_run.assert_called_once()
    args, _ = mock_run.call_args
    command = args[0]

    expected_command = ["python", "setup.py", "build", "--build-lib", str(build_dir)]
    assert command == expected_command


@patch("dagster_cloud_cli.ui.warn")
def test_build_local_package_no_build_files(mock_warn, temp_dir):
    """Test behavior when neither setup.py nor pyproject.toml exist."""
    build_dir = Path(temp_dir) / "build"
    build_dir.mkdir()

    source._build_local_package(temp_dir, str(build_dir), "python")  # noqa: SLF001

    mock_warn.assert_called_once()
    warning_msg = mock_warn.call_args[0][0]
    assert "No setup.py or pyproject.toml found" in warning_msg


def test_check_source_directory_accepts_pyproject_toml(temp_dir):
    """Test that _check_source_directory accepts directories with pyproject.toml."""
    pyproject_path = Path(temp_dir) / "pyproject.toml"
    pyproject_path.write_text("""
[project]
name = "test-package"
dependencies = ["dagster-cloud"]
""")

    # Should not raise an error
    _check_source_directory(temp_dir)


def test_check_source_directory_accepts_all_formats(tmp_path):
    """Test that all three formats (setup.py, requirements.txt, pyproject.toml) are accepted."""
    # Test each format individually
    formats = [
        ("setup.py", "from setuptools import setup; setup()"),
        ("requirements.txt", "dagster-cloud>=1.0.0\n"),
        ("pyproject.toml", "[project]\ndependencies = ['dagster-cloud']"),
    ]

    for filename, content in formats:
        format_dir = tmp_path / f"test_{filename.replace('.', '_')}"
        format_dir.mkdir()
        file_path = format_dir / filename
        file_path.write_text(content)

        # Should not raise an error for any format
        _check_source_directory(str(format_dir))


def test_check_source_directory_rejects_no_deps_file(temp_dir):
    """Test that directories without any dependency specification are rejected."""
    # Create some random file but no dependency specification
    random_file = Path(temp_dir) / "main.py"
    random_file.write_text("print('hello world')")

    with pytest.raises(ExitWithMessage):
        _check_source_directory(temp_dir)


def test_get_deps_requirements_with_pyproject_toml(temp_dir):
    """Test that get_deps_requirements correctly processes pyproject.toml projects."""
    pyproject_content = """
[project]
name = "test-package"
version = "0.1.0"
dependencies = [
    "requests>=2.25.0",
    "dagster-cloud>=1.0.0"
]

[project.optional-dependencies]
test = ["pytest>=6.0.0"]
"""

    pyproject_path = Path(temp_dir) / "pyproject.toml"
    pyproject_path.write_text(pyproject_content)

    # Create a simple Python file
    main_py = Path(temp_dir) / "main.py"
    main_py.write_text("print('Hello from pyproject.toml project')")

    local_packages, deps_requirements = deps.get_deps_requirements(
        temp_dir, version.Version("3.11.0")
    )

    # Should have no local packages (just the main directory)
    assert local_packages.local_package_paths == []

    # Should have collected dependencies from pyproject.toml
    deps_lines = deps_requirements.requirements_txt.strip().split("\n")
    deps_lines = [line.strip() for line in deps_lines if line.strip()]

    expected_deps = ["dagster-cloud>=1.0.0", "pytest>=6.0.0", "requests>=2.25.0"]
    assert sorted(deps_lines) == sorted(expected_deps)


def test_collect_requirements_with_mixed_formats(temp_dir):
    """Test collecting requirements from projects with mixed dependency formats."""
    # Create a project with pyproject.toml
    pyproject_path = Path(temp_dir) / "pyproject.toml"
    pyproject_path.write_text("""
[project]
dependencies = ["requests>=2.25.0"]
""")

    # Also create requirements.txt
    requirements_path = Path(temp_dir) / "requirements.txt"
    requirements_path.write_text("click>=8.0.0\n")

    with patch(
        "dagster_cloud_cli.core.pex_builder.deps.get_setup_py_deps",
        return_value=["setuptools>=50.0.0"],
    ):
        local_package_paths, deps_lines = deps.collect_requirements(temp_dir, "python")

        # Should collect from all sources
        expected_deps = ["click>=8.0.0", "requests>=2.25.0", "setuptools>=50.0.0"]
        assert sorted(deps_lines) == sorted(expected_deps)
        assert local_package_paths == []


def test_get_setup_py_deps_with_nested_package_structure(temp_dir):
    """Test that get_setup_py_deps works with nested package structures.

    This test reproduces a bug where setup.py egg_info was run with cwd=temp_dir
    instead of cwd=code_directory, causing it to fail to find nested packages
    and dependencies. This particularly affected multi-location builds where the
    second location would fail with empty dependencies.
    """
    # Create a nested package structure like:
    # temp_dir/
    #   setup.py
    #   my_package/
    #     __init__.py
    code_dir = Path(temp_dir)
    package_dir = code_dir / "my_package"
    package_dir.mkdir()

    # Create package __init__.py
    init_file = package_dir / "__init__.py"
    init_file.write_text("""
from dagster import Definitions, asset

@asset
def my_asset():
    return "data"

defs = Definitions(assets=[my_asset])
""")

    # Create setup.py with dependencies
    setup_py = code_dir / "setup.py"
    setup_py.write_text("""
from setuptools import find_packages, setup

setup(
    name="my-package",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "dagster>=1.0.0",
        "dagster-cloud>=1.0.0",
    ],
    extras_require={
        "dev": ["pytest>=6.0.0"]
    },
)
""")

    # Get deps using get_setup_py_deps
    deps_list = deps.get_setup_py_deps(str(code_dir), "python3")

    # Should find the dependencies from setup.py
    # Note: The exact format may include extras like 'dagster>=1.0.0' or with markers
    assert any("dagster" in dep for dep in deps_list), f"dagster not found in {deps_list}"
    assert any("dagster-cloud" in dep or "dagster_cloud" in dep for dep in deps_list), (
        f"dagster-cloud not found in {deps_list}"
    )
    assert any("pytest" in dep for dep in deps_list), f"pytest not found in {deps_list}"

    # Verify we got at least 3 dependencies
    assert len(deps_list) >= 3, (
        f"Expected at least 3 dependencies, got {len(deps_list)}: {deps_list}"
    )


def test_get_setup_py_deps_requires_correct_cwd(temp_dir):
    """Test that get_setup_py_deps runs setup.py from the correct working directory.

    This test uses a setup.py that reads a requirements file with a relative path,
    which will fail if setup.py is run from the wrong directory (i.e., cwd=temp_dir
    instead of cwd=code_directory).
    """
    code_dir = Path(temp_dir)
    package_dir = code_dir / "my_package"
    package_dir.mkdir()

    # Create package __init__.py
    (package_dir / "__init__.py").write_text(
        "from dagster import Definitions; defs = Definitions()"
    )

    # Create a requirements.txt that setup.py will read
    requirements_file = code_dir / "requirements.txt"
    requirements_file.write_text("requests>=2.25.0\n")

    # Create setup.py that reads requirements.txt with a relative path
    # This will FAIL if cwd is wrong because it won't find the file
    setup_py = code_dir / "setup.py"
    setup_py.write_text("""
from setuptools import find_packages, setup

# Read requirements from file using relative path
# This will only work if we're in the correct directory
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip()]

setup(
    name="my-package",
    version="0.1.0",
    packages=find_packages(),
    install_requires=requirements + [
        "dagster>=1.0.0",
        "dagster-cloud>=1.0.0",
    ],
)
""")

    # Get deps - this should work with correct cwd, fail with wrong cwd
    deps_list = deps.get_setup_py_deps(str(code_dir), "python3")

    # Should find all dependencies including the one from requirements.txt
    assert any("dagster" in dep for dep in deps_list), f"dagster not found in {deps_list}"
    assert any("dagster-cloud" in dep or "dagster_cloud" in dep for dep in deps_list), (
        f"dagster-cloud not found in {deps_list}"
    )
    assert any("requests" in dep for dep in deps_list), (
        f"requests from requirements.txt not found in {deps_list}"
    )

    # Verify we got at least 3 dependencies
    assert len(deps_list) >= 3, (
        f"Expected at least 3 dependencies, got {len(deps_list)}: {deps_list}"
    )


def test_get_deps_requirements_multi_location_scenario(tmp_path):
    """Test scenario that mimics multi-location build with nested packages.

    This test simulates building multiple locations sequentially, which was
    causing the second location to fail with empty dependencies due to the
    cwd bug in get_setup_py_deps.
    """
    # Use the current Python version for the test
    python_version = version.Version(f"{sys.version_info.major}.{sys.version_info.minor}")

    # Create two locations with identical nested package structure
    location1_dir = tmp_path / "location1"
    location1_dir.mkdir()
    location1_pkg = location1_dir / "location1"
    location1_pkg.mkdir()
    (location1_pkg / "__init__.py").write_text(
        "from dagster import Definitions; defs = Definitions()"
    )

    location2_dir = tmp_path / "location2"
    location2_dir.mkdir()
    location2_pkg = location2_dir / "location2"
    location2_pkg.mkdir()
    (location2_pkg / "__init__.py").write_text(
        "from dagster import Definitions; defs = Definitions()"
    )

    # Create identical setup.py files for both
    setup_content = """
from setuptools import find_packages, setup

setup(
    name="test-location",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "dagster>=1.0.0",
        "dagster-cloud>=1.0.0",
    ],
)
"""
    (location1_dir / "setup.py").write_text(setup_content)
    (location2_dir / "setup.py").write_text(
        setup_content.replace("test-location", "test-location2")
    )

    # Get deps for first location
    local_packages1, deps_requirements1 = deps.get_deps_requirements(
        str(location1_dir), python_version
    )

    # Get deps for second location - this should NOT fail with empty dependencies
    local_packages2, deps_requirements2 = deps.get_deps_requirements(
        str(location2_dir), python_version
    )

    # Both should have found dependencies
    deps1_lines = [
        line.strip()
        for line in deps_requirements1.requirements_txt.strip().split("\n")
        if line.strip()
    ]
    deps2_lines = [
        line.strip()
        for line in deps_requirements2.requirements_txt.strip().split("\n")
        if line.strip()
    ]

    # Both should have found dagster dependencies
    assert len(deps1_lines) >= 2, f"Location 1 should have at least 2 deps, got {deps1_lines}"
    assert len(deps2_lines) >= 2, f"Location 2 should have at least 2 deps, got {deps2_lines}"

    # Both should contain dagster
    assert any("dagster" in dep for dep in deps1_lines), (
        f"Location 1 missing dagster: {deps1_lines}"
    )
    assert any("dagster" in dep for dep in deps2_lines), (
        f"Location 2 missing dagster: {deps2_lines}"
    )
