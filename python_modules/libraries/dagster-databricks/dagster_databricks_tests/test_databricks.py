import dagster
import pytest
from dagster.seven import mock
from dagster.utils.test import create_test_pipeline_execution_context
from dagster_databricks.databricks import DatabricksError, DatabricksJobRunner, DatabricksRunState
from dagster_databricks.types import DatabricksRunLifeCycleState, DatabricksRunResultState

HOST = "https://uksouth.azuredatabricks.net"
TOKEN = "super-secret-token"


@mock.patch("dagster_databricks.databricks.DatabricksClient.submit_run")
def test_databricks_submit_job_existing_cluster(mock_submit_run, databricks_run_config):
    mock_submit_run.return_value = {"run_id": 1}

    runner = DatabricksJobRunner(HOST, TOKEN)
    task = databricks_run_config.pop("task")
    runner.submit_run(databricks_run_config, task)
    mock_submit_run.assert_called_once_with(
        run_name=databricks_run_config["run_name"],
        new_cluster=None,
        existing_cluster_id=databricks_run_config["cluster"]["existing"],
        spark_jar_task=task["spark_jar_task"],
        libraries=[
            {"pypi": {"package": "dagster=={}".format(dagster.__version__)}},
            {"pypi": {"package": "dagster_databricks=={}".format(dagster.__version__)}},
            {"pypi": {"package": "dagster_pyspark=={}".format(dagster.__version__)}},
        ],
    )


@mock.patch("dagster_databricks.databricks.DatabricksClient.submit_run")
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
            {"pypi": {"package": "dagster=={}".format(dagster.__version__)}},
            {"pypi": {"package": "dagster_databricks=={}".format(dagster.__version__)}},
            {"pypi": {"package": "dagster_pyspark=={}".format(dagster.__version__)}},
        ],
    )


@mock.patch("dagster_databricks.databricks.DatabricksClient.submit_run")
def test_databricks_wait_for_run(mock_submit_run, databricks_run_config):
    mock_submit_run.return_value = 1

    context = create_test_pipeline_execution_context()
    runner = DatabricksJobRunner(HOST, TOKEN, poll_interval_sec=0.01)
    task = databricks_run_config.pop("task")
    databricks_run_id = runner.submit_run(databricks_run_config, task)

    calls = {
        "num_calls": 0,
        "final_state": DatabricksRunState(
            DatabricksRunLifeCycleState.Terminated,
            DatabricksRunResultState.Success,
            "Finished",
        ),
    }

    def new_get_run_state(_run_id):
        calls["num_calls"] += 1

        if calls["num_calls"] == 1:
            return DatabricksRunState(
                DatabricksRunLifeCycleState.Pending,
                None,
                None,
            )
        elif calls["num_calls"] == 2:
            return DatabricksRunState(
                DatabricksRunLifeCycleState.Running,
                None,
                None,
            )
        else:
            return calls["final_state"]

    with mock.patch.object(runner.client, "get_run_state", new=new_get_run_state):
        runner.wait_for_run_to_complete(context.log, databricks_run_id)

    calls["num_calls"] = 0
    calls["final_state"] = DatabricksRunState(
        DatabricksRunLifeCycleState.Terminated,
        DatabricksRunResultState.Failed,
        "Failed",
    )
    with pytest.raises(DatabricksError) as exc_info:
        with mock.patch.object(runner.client, "get_run_state", new=new_get_run_state):
            runner.wait_for_run_to_complete(context.log, databricks_run_id)
    assert "Run 1 failed with result state" in str(exc_info.value)
