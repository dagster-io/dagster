import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from click.testing import CliRunner
from dagster._utils.env import environ
from dagster_dg.cli import cli as dg_cli
from dagster_dg.context import DG_UPDATE_CHECK_ENABLED_ENV_VAR
from dagster_dg.utils import pushd

from dagster_dg_tests.utils import ProxyRunner


# Runs once before every test
def pytest_configure():
    # Disable the update check for all tests because we don't want to bomb the PyPI API.
    # Tests that specifically want to test the update check should set this env var to "1".
    os.environ[DG_UPDATE_CHECK_ENABLED_ENV_VAR] = "0"


@pytest.fixture(scope="session")
def session_scaffolded_project_dir() -> Iterator[Path]:
    with (
        TemporaryDirectory() as temp_dir,
        pushd(temp_dir),
        environ(
            {
                "GIT_AUTHOR_NAME": "A Test",
                "GIT_COMMITTER_NAME": "A Test",
                "GIT_AUTHOR_EMAIL": "test@test.com",
                "GIT_COMMITTER_EMAIL": "test@test.com",
            }
        ),
    ):
        proj_dir = "foo-bar"
        CliRunner().invoke(
            dg_cli,
            ["scaffold", "project", proj_dir],
            catch_exceptions=False,
        )
        proj_path = Path(temp_dir).joinpath(proj_dir)
        subprocess.run(
            ["git", "init"],
            check=True,
            cwd=proj_path,
        )
        subprocess.run(
            ["git", "add", "."],
            check=True,
            cwd=proj_path,
        )
        subprocess.run(
            ["git", "commit", "-m", "base"],
            check=True,
            cwd=proj_path,
        )
        yield proj_path


@pytest.fixture(scope="function")
def stock_project_runner(session_scaffolded_project_dir: Path) -> Iterator[ProxyRunner]:
    """Provides a ProxyRunner with the cwd set to a freshly scaffolded project managed by git.
    Resets and cleans the repo after each test function.
    """
    with pushd(session_scaffolded_project_dir), ProxyRunner.test() as runner:
        src_dir = session_scaffolded_project_dir.joinpath("src").resolve()

        # add the src dir to the path so we can import modules in process.
        # dont insert at 0 to avoid removal by defensive code in load_python_module
        sys.path.insert(1, str(src_dir))

        try:
            yield runner
        finally:
            to_clear = set(
                k
                for k, m in sys.modules.items()
                if hasattr(m, "__file__")
                and m.__file__
                and Path(m.__file__).is_relative_to(src_dir)
            )
            for k in to_clear:
                del sys.modules[k]

            sys.path.remove(str(src_dir))
            subprocess.run(
                ["git", "reset", "HEAD", "--hard"],
                cwd=session_scaffolded_project_dir,
                check=True,
            )
            subprocess.run(
                ["git", "clean", "-fd"],
                cwd=session_scaffolded_project_dir,
                check=True,
            )
