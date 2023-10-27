from typing import Optional, Sequence

import pytest
from dagster import job
from dagster._check import CheckError
from dagster_databricks import DatabricksClientResource, databricks_client
from dagster_databricks.ops import (
    create_databricks_run_now_op,
    create_databricks_submit_run_op,
)
from databricks.sdk.service import jobs
from pytest_mock import MockerFixture


def _mock_get_run_response() -> Sequence[jobs.Run]:
    return [
        jobs.Run(
            run_name="my_databricks_run",
            run_page_url="https://abc123.cloud.databricks.com/?o=12345#job/1/run/1",
        ),
        jobs.Run(
            state=jobs.RunState(
                life_cycle_state=jobs.RunLifeCycleState.PENDING,
                state_message="",
            ),
        ),
        jobs.Run(
            state=jobs.RunState(
                life_cycle_state=jobs.RunLifeCycleState.RUNNING,
                state_message="",
            ),
        ),
        jobs.Run(
            state=jobs.RunState(
                result_state=jobs.RunResultState.SUCCESS,
                life_cycle_state=jobs.RunLifeCycleState.TERMINATED,
                state_message="Finished",
            ),
        ),
    ]


@pytest.fixture(params=["pythonic", "legacy"])
def databricks_client_factory(request):
    if request.param == "pythonic":
        return DatabricksClientResource
    else:
        return lambda **kwargs: databricks_client.configured(kwargs)


@pytest.mark.parametrize(
    "databricks_job_configuration,databricks_resource_key",
    [
        (None, None),
        ({}, "databricks"),
        (
            {
                "python_params": [
                    "--input",
                    "schema.db.input_table",
                    "--output",
                    "schema.db.output_table",
                ]
            },
            "custom_databricks_resource_key",
        ),
    ],
    ids=[
        "no Databricks job configuration, no databricks resource key",
        "empty Databricks job configuration, and default databricks resource key",
        "Databricks job configuration with python params and custom databricks resource key",
    ],
)
def test_databricks_run_now_op(
    databricks_client_factory,
    mocker: MockerFixture,
    databricks_job_configuration: Optional[dict],
    databricks_resource_key: Optional[str],
) -> None:
    mock_run_now = mocker.patch("databricks.sdk.JobsAPI.run_now")
    mock_get_run = mocker.patch("databricks.sdk.JobsAPI.get_run")
    databricks_job_id = 10

    mock_run_now_response = mocker.Mock()
    mock_run_now_response.bind.return_value = {"run_id": 1}
    mock_run_now.return_value = mock_run_now_response
    mock_get_run.side_effect = _mock_get_run_response()

    if databricks_resource_key is not None:
        test_databricks_run_now_op = create_databricks_run_now_op(
            databricks_job_id=databricks_job_id,
            databricks_job_configuration=databricks_job_configuration,
            poll_interval_seconds=0.01,
            databricks_resource_key=databricks_resource_key,
        )
    else:
        test_databricks_run_now_op = create_databricks_run_now_op(
            databricks_job_id=databricks_job_id,
            databricks_job_configuration=databricks_job_configuration,
            poll_interval_seconds=0.01,
        )

    databricks_resource_name = (
        databricks_resource_key if databricks_resource_key is not None else "databricks"
    )

    @job(
        resource_defs={
            databricks_resource_name: databricks_client_factory(
                host="https://abc123.cloud.databricks.com/", token="token"
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
    "databricks_resource_key",
    [None, "databricks", "custom_databricks_resource_key"],
    ids=[
        "no databricks resource key",
        "default databricks resource key",
        "custom databricks resource key",
    ],
)
def test_databricks_submit_run_op(
    databricks_client_factory,
    mocker: MockerFixture,
    databricks_resource_key: Optional[str],
) -> None:
    mock_submit_run = mocker.patch("databricks.sdk.JobsAPI.submit")
    mock_get_run = mocker.patch("databricks.sdk.JobsAPI.get_run")
    databricks_job_configuration = {
        "new_cluster": {
            "spark_version": "2.1.0-db3-scala2.11",
            "num_workers": 2,
        },
        "notebook_task": {
            "notebook_path": "/Users/dagster@example.com/PrepareData",
        },
    }

    mock_submit_run_response = mocker.Mock()
    mock_submit_run_response.bind.return_value = {"run_id": 1}
    mock_submit_run.return_value = mock_submit_run_response
    mock_get_run.side_effect = _mock_get_run_response()

    if databricks_resource_key is not None:
        test_databricks_submit_run_op = create_databricks_submit_run_op(
            databricks_job_configuration=databricks_job_configuration,
            poll_interval_seconds=0.01,
            databricks_resource_key=databricks_resource_key,
        )
    else:
        test_databricks_submit_run_op = create_databricks_submit_run_op(
            databricks_job_configuration=databricks_job_configuration,
            poll_interval_seconds=0.01,
        )

    databricks_resource_name = (
        databricks_resource_key if databricks_resource_key is not None else "databricks"
    )

    @job(
        resource_defs={
            databricks_resource_name: databricks_client_factory(
                host="https://abc123.cloud.databricks.com/", token="token"
            )
        }
    )
    def test_databricks_job() -> None:
        test_databricks_submit_run_op()

    result = test_databricks_job.execute_in_process()

    assert result.success
    mock_submit_run.assert_called_once_with(
        tasks=[jobs.SubmitTask.from_dict(databricks_job_configuration)],
    )
    assert mock_get_run.call_count == 4


def test_databricks_submit_run_op_no_job() -> None:
    with pytest.raises(CheckError):
        create_databricks_submit_run_op(databricks_job_configuration={})


def test_databricks_op_name():
    databricks_job_configuration = {
        "new_cluster": {
            "spark_version": "2.1.0-db3-scala2.11",
            "num_workers": 2,
        },
        "notebook_task": {
            "notebook_path": "/Users/dagster@example.com/PrepareData",
        },
    }

    @job
    def databricks_job():
        create_databricks_run_now_op(
            databricks_job_id=1,
        )()
        create_databricks_run_now_op(databricks_job_id=1, name="other_name")()
        create_databricks_submit_run_op(databricks_job_configuration)()
        create_databricks_submit_run_op(databricks_job_configuration, name="other_name_2")()
