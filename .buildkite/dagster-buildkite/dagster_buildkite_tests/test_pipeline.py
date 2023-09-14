import os
import subprocess
import tempfile
import venv

import git
import pytest
import yaml


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


class StepSummary:
    def __init__(self, step):
        self.name = step.get("label")
        self.skipped = bool(step.get("skip"))
        self.skip_reason = step.get("skip")

    def __repr__(self):
        return self.name


class PipelineSummary:
    def __init__(self, pipeline):
        planned = []
        skipped = []

        steps = pipeline["steps"]
        for step in steps:
            if step.get("label"):
                summary = StepSummary(step)
                if summary.skipped:
                    skipped.append(summary)
                else:
                    planned.append(summary)
            elif step.get("steps"):
                recursed = PipelineSummary(step)
                planned.extend(recursed.planned)
                skipped.extend(recursed.skipped)
            else:
                raise

        self.planned = planned
        self.skipped = skipped


def test_dagster_buildkite(env, dagster_buildkite):
    subprocess.run(dagster_buildkite, check=True)


def test_release_branch(env, dagster_buildkite, monkeypatch):
    monkeypatch.setenv("BUILDKITE_BRANCH", "release-0.0.1")

    pipeline = yaml.safe_load(
        subprocess.run(
            dagster_buildkite,
            capture_output=True,
        ).stdout,
    )
    summary = PipelineSummary(pipeline)

    # Nothing gets skipped
    assert not summary.skipped

    # We test multiple python versions
    assert any(["3.8" in step.name for step in summary.planned])
    assert any(["3.10" in step.name for step in summary.planned])


@pytest.mark.xfail(reason="dagster-airflow is running 3.8 tests", strict=True)
def test_main_branch(env, dagster_buildkite, monkeypatch):
    monkeypatch.setenv("BUILDKITE_BRANCH", "master")

    pipeline = yaml.safe_load(
        subprocess.run(
            dagster_buildkite,
            capture_output=True,
        ).stdout,
    )
    summary = PipelineSummary(pipeline)

    # We only test latest python versions
    assert not any(["3.8" in step.name for step in summary.planned])
    assert any(["3.10" in step.name for step in summary.planned])

    # Only our test-project builds are skipped
    assert all(["test-project" in step.name for step in summary.skipped])
