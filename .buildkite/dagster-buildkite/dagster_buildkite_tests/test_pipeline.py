import os
import subprocess
import tempfile
import venv

import git
import pytest


@pytest.fixture(scope="session")
def temporary_directory():
    with tempfile.TemporaryDirectory() as path:
        os.chdir(path)
        yield path


@pytest.fixture(scope="session")
def python(temporary_directory):
    path = os.path.join(temporary_directory, ".venv")
    venv.create(path, with_pip=True)

    python = os.path.join(path, "bin", "python")

    yield python


@pytest.fixture(scope="session")
def dagster_repo(temporary_directory, python):
    path = os.path.join(temporary_directory, "dagster")

    repo = git.Repo.clone_from(
        "https://github.com/dagster-io/dagster.git",
        path,
        filter=["tree:0"],
    )

    os.chdir(path)

    yield repo


@pytest.fixture(scope="session")
def dagster_buildkite(python, dagster_repo):
    subprocess.run(
        [python, "-m", "pip", "install", "-e", ".buildkite/dagster-buildkite"],
        check=True,
    )
    yield python.replace("python", "dagster-buildkite")


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("BUILDKITE_BRANCH", "fake")
    monkeypatch.setenv("BUILDKITE_DOCKER_QUEUE", "fake")
    monkeypatch.setenv("BUILDKITE_MEDIUM_QUEUE", "fake")
    monkeypatch.setenv("BUILDKITE_WINDOWS_QUEUE", "fake")
    monkeypatch.setenv("BUILDKITE_COMMIT", "fake")
    monkeypatch.setenv("BUILDKITE_MESSAGE", "fake")


def test_dagster_buildkite(env, dagster_buildkite):
    subprocess.run(dagster_buildkite, check=True)
