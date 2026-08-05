import os
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
from dagster_cloud.auth.constants import get_hardcoded_test_agent_token
from dagster_cloud_cli.commands.serverless import build_python_executable_command
from dagster_cloud_cli.core.pex_builder import util
from dagster_cloud_cli.core.pex_builder.deps import BuildMethod

from dagster_cloud_tests import gen_agent_instance


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--agent-batching-enabled",
        action="store_true",
        default=False,
        help="Enable agent api response batching",
    )


@pytest.fixture(scope="session", autouse=True)
def enable_agent_batching(pytestconfig):
    """Enable agent batching, iff pytest is invoked with --agent-batching-enabled."""
    batching_enabled = pytestconfig.getoption("agent_batching_enabled")
    os.environ["DAGSTER_CLOUD_AGENT_UPLOAD_API_RESPONSE_BATCHING_ENABLED"] = (
        "true" if batching_enabled else "false"
    )


@pytest.fixture(scope="module")
def agent_token():
    return get_hardcoded_test_agent_token("acme")


@pytest.fixture
def dagster_cloud_url():
    return "https://agent-api-test.dagster.cloud"


@pytest.fixture
def agent_instance(dagster_cloud_url):
    with gen_agent_instance(dagster_cloud_url, "token") as instance:
        yield instance


@pytest.fixture(scope="session")
def sample_repos_dir():
    # Returns a Path object the ./sample-repos folder
    # Usage:
    # (sample_repos_dir / 'repo-1') -> Path('/full/path/to/tmp/repo-1')
    return Path(__file__).parent / "sample-repos"


class CachingPexBuilder:
    def __init__(self, source_repos_dir, build_dir):
        self.source_repos_dir = Path(source_repos_dir)
        self.build_dir = Path(build_dir)

    def __getitem__(self, repo_name: str):
        repo_dir = self.source_repos_dir / repo_name
        if not repo_dir.exists():
            raise ValueError(f"Could not find repo {repo_name} under {self.source_repos_dir}")

        repo_build_dir = self.build_dir / repo_name

        if not repo_build_dir.exists():
            self.build_pex_files(repo_dir, repo_build_dir)
        return self.files_from_repo_build_dir(repo_build_dir)

    def files_from_repo_build_dir(self, repo_build_dir: Path):
        files: dict[str, Any] = {"all": [], "deps": [], "source": None}
        for path in repo_build_dir.iterdir():
            if path.name == ".pex" or not path.name.endswith(".pex"):
                continue
            files["all"].append(path)
            if path.name.startswith("source-"):
                files["source"] = path
            else:
                files["deps"].append(path)

        files["pex_tag"] = "files=" + ":".join(sorted(filepath.name for filepath in files["all"]))
        return files

    def build_pex_files(self, repo_source_dir, repo_build_dir):
        with mock.patch("dagster_cloud_cli.commands.metrics.gql"):
            build_python_executable_command(
                code_directory=repo_source_dir,
                output_directory=repo_build_dir,
                python_version="3.12",
                api_token="fake",
                url="fake",
                build_method=BuildMethod.LOCAL,
            )


@pytest.fixture(scope="session")
def sample_repos_pex_files(sample_repos_dir, patched_pex_flags):
    with tempfile.TemporaryDirectory() as build_dir:
        yield CachingPexBuilder(sample_repos_dir, build_dir)


@pytest.fixture(scope="session")
def patched_pex_flags(session_mocker):
    # to enable local testing for pex builds on mac:
    # - if arch is linux we assume it is CICD and leave the pex flags as-is
    # - otherwise, assume local test and set the pex platform to 'current'

    orig_get_pex_flags = util.get_pex_flags

    def get_pex_flags_patched(*args, **kwargs):
        flags = orig_get_pex_flags(*args, **kwargs)
        new_flags = []
        for flag in flags:
            if flag.startswith("--platform"):
                new_flags.append("--platform=current")
            else:
                new_flags.append(flag)

        return new_flags

    if sys.platform != "linux":
        session_mocker.patch(
            "dagster_cloud_cli.core.pex_builder.util.get_pex_flags", get_pex_flags_patched
        )

    yield


@pytest.fixture
def venvs_root(monkeypatch):
    with tempfile.TemporaryDirectory() as venv_dir:
        monkeypatch.setenv("VENVS_ROOT", venv_dir)
        yield Path(venv_dir)
