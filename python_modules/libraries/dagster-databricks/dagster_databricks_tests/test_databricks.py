from unittest import mock

import dagster
import dagster_databricks
import dagster_pyspark
import pytest
from dagster import build_op_context
from dagster_databricks.databricks import DatabricksClient, DatabricksError, DatabricksJobRunner
from dagster_databricks.types import (
    DatabricksRunLifeCycleState,
    DatabricksRunResultState,
)
from pytest_mock import MockerFixture

HOST = "https://uksouth.azuredatabricks.net"
TOKEN = "super-secret-token"


@mock.patch("databricks_cli.sdk.JobsService.submit_run")
def test_databricks_submit_job_existing_cluster(mock_submit_run, databricks_run_config):
    mock_submit_run.return_value = {"run_id": 1}

    runner = DatabricksJobRunner(HOST, TOKEN)
    task = databricks_run_config.pop("task")
    runner.submit_run(databricks_run_config, task)
    mock_submit_run.assert_called_with(
        run_name=databricks_run_config["run_name"],
        new_cluster=None,
        existing_cluster_id=databricks_run_config["cluster"]["existing"],
        spark_jar_task=task["spark_jar_task"],
        libraries=[
            {"pypi": {"package": f"dagster=={dagster.__version__}"}},
            {"pypi": {"package": f"dagster-databricks=={dagster_databricks.__version__}"}},
            {"pypi": {"package": f"dagster-pyspark=={dagster_pyspark.__version__}"}},
        ],
    )

    databricks_run_config["install_default_libraries"] = False
    runner.submit_run(databricks_run_config, task)
    mock_submit_run.assert_called_with(
        run_name=databricks_run_config["run_name"],
        new_cluster=None,
        existing_cluster_id=databricks_run_config["cluster"]["existing"],
        spark_jar_task=task["spark_jar_task"],
        libraries=[],
    )


@mock.patch("databricks_cli.sdk.JobsService.submit_run")
def test_databricks_submit_job_new_cluster(mock_submit_run, databricks_run_config):
    mock_submit_run.return_value = {"run_id": 1}

    runner = DatabricksJobRunner(HOST, TOKEN)

    NEW_CLUSTER = {
        "size": {"num_workers": 1},
        "spark_version": "6.5.x-scala2.11",
        "nodes": {"node_types": {"node_type_id": "Standard_DS3_v2"}},
    }
    databricks_run_config["cluster"] = {"new": NEW_CLUSTER}

    task = databricks_run_config.pop("task")
    runner.submit_run(databricks_run_config, task)
    mock_submit_run.assert_called_once_with(
        run_name=databricks_run_config["run_name"],
        new_cluster={
            "num_workers": 1,
            "spark_version": "6.5.x-scala2.11",
            "node_type_id": "Standard_DS3_v2",
            "custom_tags": [{"key": "__dagster_version", "value": dagster.__version__}],
        },
        existing_cluster_id=None,
        spark_jar_task=task["spark_jar_task"],
        libraries=[
            {"pypi": {"package": f"dagster=={dagster.__version__}"}},
            {"pypi": {"package": f"dagster-databricks=={dagster_databricks.__version__}"}},
            {"pypi": {"package": f"dagster-pyspark=={dagster_pyspark.__version__}"}},
        ],
    )


def test_databricks_wait_for_run(mocker: MockerFixture):
    context = build_op_context()
    mock_submit_run = mocker.patch("databricks_cli.sdk.JobsService.submit_run")
    mock_get_run = mocker.patch("databricks_cli.sdk.JobsService.get_run")

    mock_submit_run.return_value = {"run_id": 1}

    databricks_client = DatabricksClient(host=HOST, token=TOKEN)

    calls = {
        "num_calls": 0,
        "final_state": {
            "state": {
                "result_state": DatabricksRunResultState.SUCCESS,
                "life_cycle_state": DatabricksRunLifeCycleState.TERMINATED,
                "state_message": "Finished",
            }
        },
    }

    def _get_run(*args, **kwargs) -> dict:
        calls["num_calls"] += 1

        if calls["num_calls"] == 1:
            return {
                "state": {
                    "life_cycle_state": DatabricksRunLifeCycleState.PENDING,
                    "state_message": "",
                }
            }
        elif calls["num_calls"] == 2:
            return {
                "state": {
                    "life_cycle_state": DatabricksRunLifeCycleState.RUNNING,
                    "state_message": "",
                }
            }
        else:
            return calls["final_state"]

    mock_get_run.side_effect = _get_run

    databricks_client.wait_for_run_to_complete(
        logger=context.log,
        databricks_run_id=1,
        poll_interval_sec=0.01,
        max_wait_time_sec=10,
        verbose_logs=True,
    )

    calls["num_calls"] = 0
    calls["final_state"] = {
        "state": {
            "result_state": None,
            "life_cycle_state": DatabricksRunLifeCycleState.SKIPPED,
            "state_message": "Skipped",
        }
    }

    databricks_client.wait_for_run_to_complete(
        logger=context.log,
        databricks_run_id=1,
        poll_interval_sec=0.01,
        max_wait_time_sec=10,
        verbose_logs=True,
    )

    calls["num_calls"] = 0
    calls["final_state"] = {
        "state": {
            "result_state": DatabricksRunResultState.FAILED,
            "life_cycle_state": DatabricksRunLifeCycleState.TERMINATED,
            "state_message": "Failed",
        }
    }

    with pytest.raises(DatabricksError) as exc_info:
        databricks_client.wait_for_run_to_complete(
            logger=context.log,
            databricks_run_id=1,
            poll_interval_sec=0.01,
            max_wait_time_sec=10,
            verbose_logs=True,
        )

    assert "Run `1` failed with result state" in str(exc_info.value)


def test_dagster_databricks_user_agent() -> None:
    databricks_client = DatabricksClient(host=HOST, token=TOKEN)
    assert "dagster-databricks" in databricks_client.api_client.default_headers["user-agent"]

    # Remove this once databricks_api is deprecated
    assert "dagster-databricks" in databricks_client.client.client.default_headers["user-agent"]
