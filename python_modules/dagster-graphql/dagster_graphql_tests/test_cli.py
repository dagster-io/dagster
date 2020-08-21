import json
import os
import time
from contextlib import contextmanager

from click.testing import CliRunner
from dagster_graphql.cli import ui

from dagster import (
    InputDefinition,
    Int,
    OutputDefinition,
    ScheduleDefinition,
    lambda_solid,
    pipeline,
    repository,
    seven,
    solid,
)
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.utils import file_relative_path


@contextmanager
def dagster_cli_runner():
    with seven.TemporaryDirectory() as dagster_home_temp:
        yield CliRunner(env={"DAGSTER_HOME": dagster_home_temp})


@lambda_solid(input_defs=[InputDefinition("num", Int)], output_def=OutputDefinition(Int))
def add_one(num):
    return num + 1


@lambda_solid(input_defs=[InputDefinition("num", Int)], output_def=OutputDefinition(Int))
def mult_two(num):
    return num * 2


@pipeline
def math():
    mult_two(add_one())


@solid(config_schema={"gimme": str})
def needs_config(context):
    return context.solid_config["gimme"]


@lambda_solid
def no_config():
    return "ok"


@pipeline
def subset_test():
    no_config()
    needs_config()


def define_schedules():
    math_hourly_schedule = ScheduleDefinition(
        name="math_hourly_schedule",
        cron_schedule="0 0 * * *",
        pipeline_name="math",
        run_config={"solids": {"add_one": {"inputs": {"num": {"value": 123}}}}},
    )

    return [math_hourly_schedule]


@repository
def test():
    return [math, subset_test] + define_schedules()


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


def test_basic_variables():
    query = """
    query FooBar($pipelineName: String! $repositoryName: String! $repositoryLocationName: String!){
        pipelineOrError(params:{pipelineName: $pipelineName repositoryName: $repositoryName repositoryLocationName: $repositoryLocationName})
        { ... on Pipeline { name } }
    }
    """
    variables = '{"pipelineName": "math", "repositoryName": "test", "repositoryLocationName": "<<in_process>>"}'
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
        ... on LaunchPipelineRunSuccess {
            run {
                runId
                pipeline { ...on PipelineReference { name } }
            }
        }
        ... on PipelineConfigValidationInvalid {
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
    variables = seven.json.dumps(
        {
            "executionParams": {
                "selector": {
                    "repositoryLocationName": "<<in_process>>",
                    "repositoryName": "test",
                    "pipelineName": "math",
                },
                "runConfigData": {"solids": {"add_one": {"inputs": {"num": {"value": 123}}}}},
                "mode": "default",
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
                result_data["data"]["launchPipelineExecution"]["__typename"]
                == "LaunchPipelineRunSuccess"
            )
        except Exception as e:
            raise Exception("Failed with {} Exception: {}".format(result.output, e))


def test_start_execution_file():
    variables = seven.json.dumps(
        {
            "executionParams": {
                "selector": {
                    "pipelineName": "math",
                    "repositoryLocationName": "<<in_process>>",
                    "repositoryName": "test",
                },
                "runConfigData": {"solids": {"add_one": {"inputs": {"num": {"value": 123}}}}},
                "mode": "default",
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
        assert (
            result_data["data"]["launchPipelineExecution"]["__typename"]
            == "LaunchPipelineRunSuccess"
        )


def test_start_execution_save_output():
    """
    Test that the --output flag saves the GraphQL response to the specified file
    """

    variables = seven.json.dumps(
        {
            "executionParams": {
                "selector": {
                    "repositoryLocationName": "<<in_process>>",
                    "repositoryName": "test",
                    "pipelineName": "math",
                },
                "runConfigData": {"solids": {"add_one": {"inputs": {"num": {"value": 123}}}}},
                "mode": "default",
            }
        }
    )

    workspace_path = file_relative_path(__file__, "./cli_test_workspace.yaml")

    with dagster_cli_runner() as runner:
        with seven.TemporaryDirectory() as temp_dir:
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
            with open(file_name, "r") as f:
                lines = f.readlines()
                result_data = json.loads(lines[-1])
                assert (
                    result_data["data"]["launchPipelineExecution"]["__typename"]
                    == "LaunchPipelineRunSuccess"
                )


def test_start_execution_predefined():
    variables = seven.json.dumps(
        {
            "executionParams": {
                "selector": {
                    "repositoryLocationName": "<<in_process>>",
                    "repositoryName": "test",
                    "pipelineName": "math",
                },
                "runConfigData": {"solids": {"add_one": {"inputs": {"num": {"value": 123}}}}},
                "mode": "default",
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
        assert (
            result_data["data"]["launchPipelineExecution"]["__typename"]
            == "LaunchPipelineRunSuccess"
        )


def test_logs_in_start_execution_predefined():
    variables = seven.json.dumps(
        {
            "executionParams": {
                "selector": {
                    "repositoryLocationName": "<<in_process>>",
                    "repositoryName": "test",
                    "pipelineName": "math",
                },
                "runConfigData": {"solids": {"add_one": {"inputs": {"num": {"value": 123}}}}},
                "mode": "default",
            }
        }
    )

    workspace_path = file_relative_path(__file__, "./cli_test_workspace.yaml")
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)

        runner = CliRunner(env={"DAGSTER_HOME": temp_dir})
        result = runner.invoke(
            ui, ["-w", workspace_path, "-v", variables, "-p", "launchPipelineExecution"]
        )
        assert result.exit_code == 0
        result_data = json.loads(result.output.strip("\n").split("\n")[-1])
        assert (
            result_data["data"]["launchPipelineExecution"]["__typename"]
            == "LaunchPipelineRunSuccess"
        )
        run_id = result_data["data"]["launchPipelineExecution"]["run"]["runId"]

        # allow FS events to flush
        retries = 5
        while retries != 0 and not _is_done(instance, run_id):
            time.sleep(0.333)
            retries -= 1

        # assert that the watching run storage captured the run correctly from the other process
        run = instance.get_run_by_id(run_id)

        assert run.status == PipelineRunStatus.SUCCESS


def _is_done(instance, run_id):
    return instance.has_run(run_id) and instance.get_run_by_id(run_id).is_finished


def test_solid_selection():
    variables = seven.json.dumps(
        {
            "executionParams": {
                "mode": "default",
                "runConfigData": {},
                "selector": {
                    "repositoryLocationName": "<<in_process>>",
                    "repositoryName": "test",
                    "pipelineName": "subset_test",
                    "solidSelection": ["no_config"],
                },
                "executionMetadata": {"runId": "1234"},
                "stepKeys": ["no_config.compute"],
            },
        }
    )
    workspace_path = file_relative_path(__file__, "./cli_test_workspace.yaml")

    with dagster_cli_runner() as runner:
        result = runner.invoke(ui, ["-w", workspace_path, "-v", variables, "-p", "executePlan"])

        assert result.exit_code == 0

        try:
            result_data = json.loads(result.output.strip("\n").split("\n")[-1])
            assert result_data["data"]["executePlan"]["__typename"] == "ExecutePlanSuccess"
        except Exception as e:
            raise Exception("Failed with {} Exception: {}".format(result.output, e))
