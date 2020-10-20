import pytest
from dagster import ModeDefinition, execute_pipeline, pipeline
from dagster.seven import mock
from dagster_databricks import create_databricks_job_solid, databricks_client
from dagster_databricks.databricks import DatabricksRunState
from dagster_databricks.solids import create_ui_url
from dagster_databricks.types import DatabricksRunLifeCycleState, DatabricksRunResultState


@mock.patch("dagster_databricks.databricks.DatabricksClient.get_run_state")
@mock.patch("dagster_databricks.databricks.DatabricksClient.submit_run")
def test_run_create_databricks_job_solid(
    mock_submit_run, mock_get_run_state, databricks_run_config
):
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
        create_databricks_job_solid(num_inputs=0).configured(
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
    assert mock_submit_run.call_args_list[0] == (databricks_run_config,)
    assert mock_get_run_state.call_count == 1
    assert mock_get_run_state.call_args[0][0] == RUN_ID


def test_create_databricks_job_solid_args():
    assert create_databricks_job_solid().name == "databricks_job"
    assert create_databricks_job_solid("my_name").name == "my_name"
    assert len(create_databricks_job_solid().input_defs) == 1
    assert len(create_databricks_job_solid(num_inputs=2).input_defs) == 2
    assert len(create_databricks_job_solid().output_defs) == 1


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
