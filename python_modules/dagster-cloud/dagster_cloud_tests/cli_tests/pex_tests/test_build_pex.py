import subprocess
import tempfile
from pathlib import Path

import dagster_cloud_cli.core.pex_builder.util
import pytest
from dagster_cloud_cli.entrypoint import app
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_gql(mocker):
    yield mocker.patch("dagster_cloud_cli.commands.serverless.metrics.gql", autospec=True)


def build_dagster_project(code_directory):
    with tempfile.TemporaryDirectory() as build_dir:
        result = runner.invoke(
            app,
            [
                "serverless",
                "build-python-executable",
                "--python-version=3.12",
                str(code_directory),
                build_dir,
            ],
            env={
                "DAGSTER_CLOUD_API_TOKEN": "fake",
                "DAGSTER_CLOUD_ORGANIZATION": "fake",
                "DAGSTER_CLOUD_DEPLOYMENT": "fake",
            },
        )
        assert result.exit_code == 0, f"Failed to build {code_directory}: {result.output}"
        assert "Built" in result.stdout

        build_path = Path(build_dir)
        pex_files = [
            path for path in build_path.iterdir() if path.name.endswith(".pex") and path.is_file()
        ]
        assert len(pex_files) == 2


def test_build_python_executable(sample_repos_dir):
    build_dagster_project(str(sample_repos_dir / "repo-1"))


def test_build_quickstart_etl():
    import dagster

    build_dagster_project(Path(dagster.__file__).parents[3] / "examples/quickstart_etl")


def test_build_methods(sample_repos_dir, mocker):
    # mock pex builder function to allow forcing failure using deps_build_stderr
    orig_build_pex = dagster_cloud_cli.core.pex_builder.util.build_pex
    deps_build_stderr = None

    def build_pex_fail_deps(
        sources_directories: list[str],
        requirements_filepaths: list[str],
        pex_flags: list[str],
        output_pex_path: str,
        pex_root: str | None = None,
    ):
        if requirements_filepaths and deps_build_stderr is not None:
            return subprocess.CompletedProcess(["testmock"], 1, b"stdout", deps_build_stderr)
        return orig_build_pex(
            sources_directories, requirements_filepaths, pex_flags, output_pex_path, pex_root
        )

    build_pex = mocker.patch(
        "dagster_cloud_cli.core.pex_builder.util.build_pex", side_effect=build_pex_fail_deps
    )
    docker_runner_dagster_cloud = mocker.patch(
        "dagster_cloud_cli.core.docker_runner.run_dagster_cloud", autospec=True
    )

    def build_repo(extra_args=[]):
        code_directory = str(sample_repos_dir / "repo-1")
        with tempfile.TemporaryDirectory() as build_dir:
            return runner.invoke(
                app,
                [
                    "serverless",
                    "build-python-executable",
                    "--python-version=3.12",
                    str(code_directory),
                    build_dir,
                ]
                + extra_args,
                env={
                    "DAGSTER_CLOUD_API_TOKEN": "fake",
                    "DAGSTER_CLOUD_ORGANIZATION": "fake",
                    "DAGSTER_CLOUD_DEPLOYMENT": "fake",
                },
            )

    # build fails for unknown reason: should propagate
    deps_build_stderr = b"stderr123"
    result = build_repo(["--build-method=docker-fallback"])
    assert result.exit_code != 0, f"failure did not propgate: {result.output}"
    assert "stderr123" in result.output
    build_pex.assert_called_once()
    docker_runner_dagster_cloud.assert_not_called()

    # build fails due to ResolutionImpossible: should try and fallback to docker
    build_pex.reset_mock()
    docker_runner_dagster_cloud.reset_mock()
    deps_build_stderr = b"ResolutionImpossible"
    result = build_repo(["--build-method=docker-fallback"])
    build_pex.assert_called_once()
    docker_runner_dagster_cloud.assert_called_once()
    call_args = docker_runner_dagster_cloud.call_args
    assert "build-python-deps" in call_args.kwargs["run_args"]

    # when --build-method==local, don't fallback to docker
    build_pex.reset_mock()
    docker_runner_dagster_cloud.reset_mock()
    deps_build_stderr = b"ResolutionImpossible"
    result = build_repo(["--build-method=local"])
    build_pex.assert_called_once()
    docker_runner_dagster_cloud.assert_not_called()
    assert result.exit_code != 0, f"failure did not propgate: {result.output}"

    # when --build-method=local and no failure, dont fallback to docker
    build_pex.reset_mock()
    docker_runner_dagster_cloud.reset_mock()
    deps_build_stderr = None
    result = build_repo(["--build-method=local"])
    build_pex.assert_called()  # would be called twice - once for source and once for deps
    docker_runner_dagster_cloud.assert_not_called()
    assert result.exit_code == 0

    # when --build-method==docker, don't try to build locally, just in docker
    build_pex.reset_mock()
    docker_runner_dagster_cloud.reset_mock()
    deps_build_stderr = b"stderr456"
    result = build_repo(["--build-method=docker"])
    build_pex.assert_not_called()  # local build not attempted
    docker_runner_dagster_cloud.assert_called_once()
