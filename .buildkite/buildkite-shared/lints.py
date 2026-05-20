"""Lints that enforce certain assumptions our build makes."""

import configparser
import os
import subprocess
from pathlib import Path

import pytest


def find_tox_ini() -> list[str]:
    tox_files = []
    for root, dirs, files in os.walk("."):
        if "tox.ini" in files:
            tox_file = os.path.join(root, "tox.ini")
            tox_files.append(tox_file)
    return tox_files


@pytest.fixture(params=find_tox_ini(), ids=lambda i: i)
def tox_config(request: pytest.FixtureRequest) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(request.param)

    assert "testenv" in config
    assert "passenv" in config["testenv"]

    return config


def test_tox_passenv(tox_config: configparser.ConfigParser) -> None:
    PASSENV_ENV = [
        "BUILDKITE*",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
    ]

    missing_env = []
    for env in PASSENV_ENV:
        if env not in tox_config["testenv"]["passenv"].split("\n"):
            missing_env.append(env)

    assert not missing_env, f"tox.ini missing passenv {missing_env}"


def test_no_subdirectory_pytest_ini() -> None:
    pytest_ini_files = []
    for root, dirs, files in os.walk("."):
        if "pytest.ini" in files:
            pytest_ini_file = os.path.join(root, "tox.ini")
            pytest_ini_files.append(pytest_ini_file)

    assert not pytest_ini_files, (
        f"Subdirectory pytest.ini files conflict with our root pyproject.toml settings and conftest.py discovery. Please remove: {pytest_ini_files}"
    )


def test_no_tox_pytest_config_override(tox_config: configparser.ConfigParser) -> None:
    if "commands" in tox_config["testenv"]:
        assert "pyproject.toml" not in tox_config["testenv"]["commands"], (
            "We use a global PYTEST_CONFIG that uses the root directory's pyproject.toml. Remove any -c overrides in pytest commands in tox.ini"
        )


@pytest.fixture(params=find_tox_ini(), ids=lambda i: i)
def tox_path(request: pytest.FixtureRequest) -> str:
    return request.param


def _is_gitignored(path: Path) -> bool:
    """True if `path` is excluded by a tracked .gitignore. Used to skip packages
    that intentionally opt out of committing a uv.lock (e.g. examples/docs_snippets).
    """
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", str(path)],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def find_project_pyprojects() -> list[str]:
    """Pyproject.toml files declaring a `[project]` table (i.e. real Python packages).

    Excludes config-only pyprojects (workspace roots, ruff-only config), docs
    snippet fragments embedded under examples/docs_snippets/, and test fixtures
    that intentionally have no `[project]` table.
    """
    out: list[str] = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in {".tox", ".venv", "node_modules", "__pycache__"}]
        if "pyproject.toml" not in files:
            continue
        path = Path(root) / "pyproject.toml"
        text = path.read_text(encoding="utf-8")
        if "[project]" in text:
            out.append(str(path))
    return out


@pytest.fixture(params=find_project_pyprojects(), ids=lambda i: i)
def project_pyproject_path(request: pytest.FixtureRequest) -> str:
    return request.param


def test_pyproject_has_requires_python(project_pyproject_path: str) -> None:
    """Every pyproject.toml with a `[project]` table must set `requires-python`.

    Without an explicit `requires-python`, `uv lock` resolves across a much wider
    Python range than the package actually supports. That tends to pin deps to
    older versions to satisfy the broader range — exactly the failure mode that
    surfaced during the per-package uv.lock migration. Default to
    `>=3.10,<3.15` (matching python_modules/dagster) unless the package has a
    real compatibility constraint requiring a narrower range.
    """
    text = Path(project_pyproject_path).read_text(encoding="utf-8")
    has_requires_python = any(
        line.lstrip().startswith("requires-python") for line in text.splitlines()
    )
    assert has_requires_python, (
        f"{project_pyproject_path} declares a [project] table but no "
        f"`requires-python`. Add one (default `>=3.10,<3.15` to match "
        f"python_modules/dagster) under [project]."
    )


def test_tox_has_lockfile(tox_path: str) -> None:
    pkg_dir = Path(tox_path).parent
    pyproject = pkg_dir / "pyproject.toml"
    uv_lock = pkg_dir / "uv.lock"
    assert pyproject.exists(), (
        f"{tox_path} has no sibling pyproject.toml. Every tox-tested package must have"
        f" a pyproject.toml so its dependencies can be locked via uv. See"
        f" dagster-oss/scripts/update_lockfiles.py."
    )

    if _is_gitignored(uv_lock):
        # Package opts out of locking by gitignoring uv.lock; nothing else to check.
        return

    assert uv_lock.exists(), (
        f"{tox_path} has no sibling uv.lock. Run"
        f" `python dagster-oss/scripts/update_lockfiles.py {pkg_dir}` to generate one"
        f" (or add `uv.lock` to {pkg_dir}/.gitignore to opt out)."
    )

    config = configparser.ConfigParser()
    config.read(tox_path)
    runner = config.get("testenv", "runner", fallback="")
    assert runner == "uv-venv-lock-runner", (
        f"{tox_path} must set `runner = uv-venv-lock-runner` under [testenv] so tox"
        f" installs from the sibling uv.lock (got runner={runner!r})."
    )
    uv_sync_flags = config.get("testenv", "uv_sync_flags", fallback="")
    assert "--frozen" in uv_sync_flags, (
        f"{tox_path} must set `uv_sync_flags = --frozen` under [testenv] so the"
        f" installed env matches uv.lock exactly (got uv_sync_flags={uv_sync_flags!r})."
    )
