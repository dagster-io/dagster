from dagster_databricks import create_databricks_job_solid, databricks_client
from dagster_databricks.databricks import DatabricksRunState
from dagster_databricks.types import DatabricksRunLifeCycleState, DatabricksRunResultState

from dagster import ModeDefinition, execute_pipeline, pipeline
from dagster.seven import mock


@mock.patch("dagster_databricks.databricks.DatabricksClient.get_run_state")
@mock.patch("dagster_databricks.databricks.DatabricksClient.submit_run")
def test_create_databricks_job_solid(mock_submit_run, mock_get_run_state, databricks_run_config):
    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "databricks_client": databricks_client.configured(
                        {"host": "a", "token": "fdshj"}
                    )
                }
            )
        ]
    )
    def test_pipe():
        create_databricks_job_solid("test", num_inputs=0).configured(
            {"job": databricks_run_config, "poll_interval_sec": 0.01}, name="test"
        )()

    RUN_ID = 1
    mock_submit_run.return_value = RUN_ID
    mock_get_run_state.return_value = DatabricksRunState(
        state_message="",
        result_state=DatabricksRunResultState.Success,
        life_cycle_state=DatabricksRunLifeCycleState.Terminated,
    )

    result = execute_pipeline(test_pipe)
    assert result.success

    assert mock_submit_run.call_count == 1
    assert mock_submit_run.call_args[0][0] == databricks_run_config
    assert mock_get_run_state.call_count == 1
    assert mock_get_run_state.call_args[0][0] == RUN_ID
