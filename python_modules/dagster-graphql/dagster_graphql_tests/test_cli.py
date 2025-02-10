import json
import os
import tempfile
import time
from contextlib import contextmanager

from click.testing import CliRunner
from dagster import _seven, job, op
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.test_utils import instance_for_test
from dagster._utils import file_relative_path
from dagster_graphql.cli import ui
from dagster_graphql.client.client_queries import GET_PIPELINE_RUN_STATUS_QUERY


@contextmanager
def dagster_cli_runner():
    with tempfile.TemporaryDirectory() as dagster_home_temp:
        with instance_for_test(
            temp_dir=dagster_home_temp,
            overrides={
                "run_coordinator": {
                    "module": "dagster._core.run_coordinator.immediately_launch_run_coordinator",
                    "class": "ImmediatelyLaunchRunCoordinator",
                },
                "run_launcher": {
                    "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                    "class": "SyncInMemoryRunLauncher",
                },
            },
        ):
            yield CliRunner(env={"DAGSTER_HOME": dagster_home_temp})


def test_basic_introspection():
    query = "{ __schema { types { name } } }"

    workspace_path = file_relative_path(__file__, "./cli_test_workspace.yaml")

    with dagster_cli_runner() as runner:
        result = runner.invoke(ui, ["-w", workspace_path, "-t", query])
        assert result.exit_code == 0

        result_data = json.loads(result.output)
        assert result_data["data"]


def test_basic_repositories():
    query = "{ repositoriesOrError { ... on RepositoryConnection { nodes { name } } } }"

    workspace_path = file_relative_path(__file__, "./cli_test_workspace.yaml")

    with dagster_cli_runner() as runner:
        result = runner.invoke(ui, ["-w", workspace_path, "-t", query])

        assert result.exit_code == 0

        result_data = json.loads(result.output)
        assert result_data["data"]["repositoriesOrError"]["nodes"]


def test_async_resolver():
    @op
    def my_op():
        pass

    @job
    def my_job():
        my_op()

    with tempfile.TemporaryDirectory() as dagster_home_temp:
        with instance_for_test(
            temp_dir=dagster_home_temp,
            overrides={
                "run_coordinator": {
                    "module": "dagster._core.run_coordinator.immediately_launch_run_coordinator",
                    "class": "ImmediatelyLaunchRunCoordinator",
                },
                "run_launcher": {
                    "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                    "class": "SyncInMemoryRunLauncher",
                },
            },
        ) as instance:
            result = my_job.execute_in_process(instance=instance)
            run_id = result.dagster_run.run_id

            runner = CliRunner(env={"DAGSTER_HOME": dagster_home_temp})

            query = GET_PIPELINE_RUN_STATUS_QUERY
            variables = json.dumps({"runId": run_id})

            workspace_path = file_relative_path(__file__, "./cli_test_workspace.yaml")

            result = runner.invoke(ui, ["-w", workspace_path, "-v", variables, "-t", query])
            assert result.exit_code == 0

            result_data = json.loads(result.output)

            assert (
                result_data["data"]["pipelineRunOrError"]["status"]
                == DagsterRunStatus.SUCCESS.value
            )


def test_basic_repository_locations():
    query = (
        "{ workspaceOrError { ... on Workspace { locationEntries { __typename, name,"
        " locationOrLoadError { __typename, ... on RepositoryLocation { __typename, name } ... on"
        " PythonError { message } } } } } }"
    )

    workspace_path = file_relative_path(__file__, "./cli_test_error_workspace.yaml")

    with dagster_cli_runner() as runner:
        result = runner.invoke(ui, ["-w", workspace_path, "-t", query])

        assert result.exit_code == 0, str(result.exception)

        result_data = json.loads(result.output)

        nodes = result_data["data"]["workspaceOrError"]["locationEntries"]
        assert len(nodes) == 2, str(nodes)

        assert nodes[0]["locationOrLoadError"]["__typename"] == "RepositoryLocation"
        assert nodes[0]["name"] == "test_cli_location"

        assert nodes[1]["locationOrLoadError"]["__typename"] == "PythonError"
        assert nodes[1]["name"] == "test_cli_location_error"
        assert "No module named" in nodes[1]["locationOrLoadError"]["message"]


def test_basic_variables():
    query = """
    query FooBar($pipelineName: String! $repositoryName: String! $repositoryLocationName: String!){
        pipelineOrError(params:{pipelineName: $pipelineName repositoryName: $repositoryName repositoryLocationName: $repositoryLocationName})
        { ... on Pipeline { name } }
    }
    """
    variables = (
        '{"pipelineName": "math", "repositoryName": "test", "repositoryLocationName":'
        ' "test_cli_location"}'
    )
    workspace_path = file_relative_path(__file__, "./cli_test_workspace.yaml")

    with dagster_cli_runner() as runner:
        result = runner.invoke(ui, ["-w", workspace_path, "-v", variables, "-t", query])

        assert result.exit_code == 0

        result_data = json.loads(result.output)
        assert result_data["data"]["pipelineOrError"]["name"] == "math"


LAUNCH_PIPELINE_EXECUTION_QUERY = """
mutation ($executionParams: ExecutionParams!) {
    launchPipelineExecution(executionParams: $executionParams) {
        __typename
        ... on LaunchRunSuccess {
            run {
                runId
                pipeline { ...on PipelineReference { name } }
            }
        }
        ... on RunConfigValidationInvalid {
            pipelineName
            errors { message }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
        ... on PythonError {
            message
            stack
        }
    }
}
"""


def test_start_execution_text():
    variables = _seven.json.dumps(
        {
            "executionParams": {
                "selector": {
                    "repositoryLocationName": "test_cli_location",
                    "repositoryName": "test",
                    "pipelineName": "math",
                },
                "runConfigData": {"ops": {"add_one": {"inputs": {"num": {"value": 123}}}}},
            }
        }
    )

    workspace_path = file_relative_path(__file__, "./cli_test_workspace.yaml")

    with dagster_cli_runner() as runner:
        result = runner.invoke(
            ui, ["-w", workspace_path, "-v", variables, "-t", LAUNCH_PIPELINE_EXECUTION_QUERY]
        )

        assert result.exit_code == 0

        try:
            result_data = json.loads(result.output.strip("\n").split("\n")[-1])
            assert (
                result_data["data"]["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
            )
        except Exception as e:
            raise Exception(f"Failed with {result.output} Exception: {e}")


def test_start_execution_file():
    variables = _seven.json.dumps(
        {
            "executionParams": {
                "selector": {
                    "pipelineName": "math",
                    "repositoryLocationName": "test_cli_location",
                    "repositoryName": "test",
                },
                "runConfigData": {"ops": {"add_one": {"inputs": {"num": {"value": 123}}}}},
            }
        }
    )

    workspace_path = file_relative_path(__file__, "./cli_test_workspace.yaml")
    with dagster_cli_runner() as runner:
        result = runner.invoke(
            ui,
            [
                "-w",
                workspace_path,
                "-v",
                variables,
                "--file",
                file_relative_path(__file__, "./execute.graphql"),
            ],
        )

        assert result.exit_code == 0
        result_data = json.loads(result.output.strip("\n").split("\n")[-1])
        assert result_data["data"]["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"


def test_start_execution_save_output():
    """Test that the --output flag saves the GraphQL response to the specified file."""
    variables = _seven.json.dumps(
        {
            "executionParams": {
                "selector": {
                    "repositoryLocationName": "test_cli_location",
                    "repositoryName": "test",
                    "pipelineName": "math",
                },
                "runConfigData": {"ops": {"add_one": {"inputs": {"num": {"value": 123}}}}},
            }
        }
    )

    workspace_path = file_relative_path(__file__, "./cli_test_workspace.yaml")

    with dagster_cli_runner() as runner:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "output_file")

            result = runner.invoke(
                ui,
                [
                    "-w",
                    workspace_path,
                    "-v",
                    variables,
                    "--file",
                    file_relative_path(__file__, "./execute.graphql"),
                    "--output",
                    file_name,
                ],
            )

            assert result.exit_code == 0

            assert os.path.isfile(file_name)
            with open(file_name, encoding="utf8") as f:
                lines = f.readlines()
                result_data = json.loads(lines[-1])
                assert (
                    result_data["data"]["launchPipelineExecution"]["__typename"]
                    == "LaunchRunSuccess"
                )


def test_start_execution_predefined():
    variables = _seven.json.dumps(
        {
            "executionParams": {
                "selector": {
                    "repositoryLocationName": "test_cli_location",
                    "repositoryName": "test",
                    "pipelineName": "math",
                },
                "runConfigData": {"ops": {"add_one": {"inputs": {"num": {"value": 123}}}}},
            }
        }
    )

    workspace_path = file_relative_path(__file__, "./cli_test_workspace.yaml")

    with dagster_cli_runner() as runner:
        result = runner.invoke(
            ui, ["-w", workspace_path, "-v", variables, "-p", "launchPipelineExecution"]
        )
        assert result.exit_code == 0
        result_data = json.loads(result.output.strip("\n").split("\n")[-1])
        if not result_data.get("data"):
            raise Exception(result_data)
        assert result_data["data"]["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"


def test_logs_in_start_execution_predefined():
    variables = _seven.json.dumps(
        {
            "executionParams": {
                "selector": {
                    "repositoryLocationName": "test_cli_location",
                    "repositoryName": "test",
                    "pipelineName": "math",
                },
                "runConfigData": {"ops": {"add_one": {"inputs": {"num": {"value": 123}}}}},
            }
        }
    )

    workspace_path = file_relative_path(__file__, "./cli_test_workspace.yaml")
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(
            temp_dir=temp_dir,
            overrides={
                "run_coordinator": {
                    "module": "dagster._core.run_coordinator.immediately_launch_run_coordinator",
                    "class": "ImmediatelyLaunchRunCoordinator",
                },
                "run_launcher": {
                    "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                    "class": "SyncInMemoryRunLauncher",
                },
            },
        ) as instance:
            runner = CliRunner(env={"DAGSTER_HOME": temp_dir})
            result = runner.invoke(
                ui, ["-w", workspace_path, "-v", variables, "-p", "launchPipelineExecution"]
            )
            assert result.exit_code == 0
            result_data = json.loads(result.output.strip("\n").split("\n")[-1])
            assert (
                result_data["data"]["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
            )
            run_id = result_data["data"]["launchPipelineExecution"]["run"]["runId"]

            # allow FS events to flush
            retries = 5
            while retries != 0 and not _is_done(instance, run_id):
                time.sleep(0.333)
                retries -= 1

            # assert that the watching run storage captured the run correctly from the other process
            run = instance.get_run_by_id(run_id)

            assert run.status == DagsterRunStatus.SUCCESS  # pyright: ignore[reportOptionalMemberAccess]


def _is_done(instance, run_id):
    return instance.has_run(run_id) and instance.get_run_by_id(run_id).is_finished
