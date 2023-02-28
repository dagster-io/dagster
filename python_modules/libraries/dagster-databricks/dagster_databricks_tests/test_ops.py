from typing import Optional, Sequence
from unittest import mock

import pytest
from dagster import In, Nothing, Out, job
from dagster._check import CheckError
from dagster_databricks import create_databricks_job_op, databricks_client
from dagster_databricks.ops import (
    create_databricks_run_now_op,
    create_databricks_submit_run_op,
    create_ui_url,
)
from dagster_databricks.types import (
    DatabricksRunLifeCycleState,
    DatabricksRunResultState,
    DatabricksRunState,
)
from pytest_mock import MockerFixture


def _mock_get_run_response() -> Sequence[dict]:
    return [
        {
            "run_name": "my_databricks_run",
            "run_page_url": "https://abc123.cloud.databricks.com/?o=12345#job/1/run/1",
        },
        {
            "state": {
                "life_cycle_state": DatabricksRunLifeCycleState.PENDING,
                "state_message": "",
            }
        },
        {
            "state": {
                "life_cycle_state": DatabricksRunLifeCycleState.RUNNING,
                "state_message": "",
            }
        },
        {
            "state": {
                "result_state": DatabricksRunResultState.SUCCESS,
                "life_cycle_state": DatabricksRunLifeCycleState.TERMINATED,
                "state_message": "Finished",
            }
        },
    ]


@pytest.mark.parametrize("job_creator", [create_databricks_job_op])
@mock.patch("dagster_databricks.databricks.DatabricksClient.get_run_state")
@mock.patch("databricks_cli.sdk.JobsService.submit_run")
def test_run_create_databricks_job_op(
    mock_submit_run, mock_get_run_state, databricks_run_config, job_creator
):
    @job(
        resource_defs={
            "databricks_client": databricks_client.configured({"host": "a", "token": "fdshj"})
        }
    )
    def test_job():
        job_creator(num_inputs=0).configured(
            {"job": databricks_run_config, "poll_interval_sec": 0.01}, "test"
        )()

    RUN_ID = 1
    mock_submit_run.return_value = {"run_id": RUN_ID}
    mock_get_run_state.return_value = DatabricksRunState(
        state_message="",
        result_state=DatabricksRunResultState.SUCCESS,
        life_cycle_state=DatabricksRunLifeCycleState.TERMINATED,
    )

    result = test_job.execute_in_process()
    assert result.success

    assert mock_submit_run.call_count == 1
    assert mock_submit_run.call_args_list[0] == (databricks_run_config,)
    assert mock_get_run_state.call_count == 1
    assert mock_get_run_state.call_args[0][0] == RUN_ID


@pytest.mark.parametrize("job_creator", [create_databricks_job_op])
def test_create_databricks_job_args(job_creator):
    assert job_creator().name == "databricks_job"
    assert job_creator("my_name").name == "my_name"
    assert len(job_creator().input_defs) == 1
    assert len(job_creator(num_inputs=2).input_defs) == 2
    assert len(job_creator().output_defs) == 1


@pytest.mark.parametrize(
    "host, config, workspace_id, expected",
    [
        (
            "abc123.cloud.databricks.com",
            {"job": {"existing_cluster_id": "fdsa453fd"}},
            None,
            "https://abc123.cloud.databricks.com/?o=<workspace_id>#/setting/clusters/fdsa453fd/sparkUi",
        ),
        (
            "abc123.cloud.databricks.com",
            {"job": {"existing_cluster_id": "fdsa453fd"}},
            "56789",
            "https://abc123.cloud.databricks.com/?o=56789#/setting/clusters/fdsa453fd/sparkUi",
        ),
        (
            "abc123.cloud.databricks.com",
            {"job": {}},
            None,
            "https://abc123.cloud.databricks.com/?o=<workspace_id>#joblist",
        ),
        (
            "abc123.cloud.databricks.com",
            {"job": {}},
            "56789",
            "https://abc123.cloud.databricks.com/?o=56789#joblist",
        ),
    ],
)
def test_create_ui_url(host, config, workspace_id, expected):
    client = mock.MagicMock(host=host, workspace_id=workspace_id)
    assert create_ui_url(client, config) == expected


@pytest.mark.parametrize(
    "op_kwargs",
    [
        {},
        {
            "ins": {"input1": In(Nothing), "input2": In(Nothing)},
            "out": {
                "output1": Out(Nothing, is_required=False),
                "output2": Out(Nothing, is_required=False),
            },
        },
    ],
    ids=[
        "no overrides",
        "with ins and outs",
    ],
)
@pytest.mark.parametrize(
    "databricks_job_configuration",
    [
        None,
        {},
        {
            "python_params": [
                "--input",
                "schema.db.input_table",
                "--output",
                "schema.db.output_table",
            ]
        },
    ],
    ids=[
        "no Databricks job configuration",
        "empty Databricks job configuration",
        "Databricks job configuration with python params",
    ],
)
def test_databricks_run_now_op(
    mocker: MockerFixture, op_kwargs: dict, databricks_job_configuration: Optional[dict]
) -> None:
    mock_run_now = mocker.patch("databricks_cli.sdk.JobsService.run_now")
    mock_get_run = mocker.patch("databricks_cli.sdk.JobsService.get_run")
    databricks_job_id = 10

    mock_run_now.return_value = {"run_id": 1}
    mock_get_run.side_effect = _mock_get_run_response()

    test_databricks_run_now_op = create_databricks_run_now_op(
        databricks_job_id=databricks_job_id,
        databricks_job_configuration=databricks_job_configuration,
        **op_kwargs,
    ).configured(
        config_or_config_fn={
            "poll_interval_sec": 0.01,
        },
        name="test_databricks_run_now_op",
    )

    @job(
        resource_defs={
            "databricks": databricks_client.configured(
                {"host": "https://abc123.cloud.databricks.com/", "token": "token"}
            )
        }
    )
    def test_databricks_job() -> None:
        test_databricks_run_now_op()

    result = test_databricks_job.execute_in_process()

    assert result.success
    mock_run_now.assert_called_once_with(
        job_id=databricks_job_id,
        **(databricks_job_configuration or {}),
    )
    assert mock_get_run.call_count == 4


@pytest.mark.parametrize(
    "op_kwargs",
    [
        {},
        {
            "ins": {"input1": In(Nothing), "input2": In(Nothing)},
            "out": {
                "output1": Out(Nothing, is_required=False),
                "output2": Out(Nothing, is_required=False),
            },
        },
    ],
    ids=[
        "no overrides",
        "with ins and outs",
    ],
)
def test_databricks_submit_run_op(mocker: MockerFixture, op_kwargs: dict) -> None:
    mock_submit_run = mocker.patch("databricks_cli.sdk.JobsService.submit_run")
    mock_get_run = mocker.patch("databricks_cli.sdk.JobsService.get_run")

    mock_submit_run.return_value = {"run_id": 1}
    mock_get_run.side_effect = _mock_get_run_response()

    test_databricks_submit_run_op = create_databricks_submit_run_op(
        databricks_job_configuration={
            "new_cluster": {
                "spark_version": "2.1.0-db3-scala2.11",
                "num_workers": 2,
            },
            "notebook_task": {
                "notebook_path": "/Users/dagster@example.com/PrepareData",
            },
        },
        **op_kwargs,
    ).configured(
        config_or_config_fn={
            "poll_interval_sec": 0.01,
        },
        name="test_databricks_submit_run_op",
    )

    @job(
        resource_defs={
            "databricks": databricks_client.configured(
                {"host": "https://abc123.cloud.databricks.com/", "token": "token"}
            )
        }
    )
    def test_databricks_job() -> None:
        test_databricks_submit_run_op()

    result = test_databricks_job.execute_in_process()

    assert result.success
    assert mock_submit_run.call_count == 1
    assert mock_get_run.call_count == 4


def test_databricks_submit_run_op_no_job() -> None:
    with pytest.raises(CheckError):
        create_databricks_submit_run_op(databricks_job_configuration={})
