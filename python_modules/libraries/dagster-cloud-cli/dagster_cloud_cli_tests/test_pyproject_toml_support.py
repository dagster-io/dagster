from pathlib import Path
from unittest.mock import patch

import pytest
from dagster_cloud_cli.core.pex_builder import deps, source


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
    assert kwargs["capture_output"] is True
    assert kwargs["check"] is True


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
    from dagster_cloud_cli.commands.serverless import _check_source_directory

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
    from dagster_cloud_cli.commands.serverless import _check_source_directory

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
    from dagster_cloud_cli.commands.serverless import _check_source_directory
    from dagster_cloud_cli.ui import ExitWithMessage

    # Create some random file but no dependency specification
    random_file = Path(temp_dir) / "main.py"
    random_file.write_text("print('hello world')")

    with pytest.raises(ExitWithMessage):
        _check_source_directory(temp_dir)


def test_get_deps_requirements_with_pyproject_toml(temp_dir):
    """Test that get_deps_requirements correctly processes pyproject.toml projects."""
    from packaging import version

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
