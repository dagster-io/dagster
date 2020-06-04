from dagster_databricks import DatabricksRunJobSolidDefinition

from dagster import execute_pipeline, pipeline
from dagster.seven import mock

HOST = 'https://uksouth.azuredatabricks.net'
TOKEN = 'super-secret-token'


@mock.patch('dagster_databricks.databricks.DatabricksJobRunner.submit_run')
@mock.patch('dagster_databricks.databricks.DatabricksJobRunner.wait_for_run_to_complete')
def test_run_databricks_job(mock_wait_for_run, mock_submit_run, databricks_run_config):
    @pipeline
    def test_pipe():
        DatabricksRunJobSolidDefinition('test', poll_interval_sec=1)()

    RUN_ID = 1
    mock_submit_run.return_value = RUN_ID

    config = {
        'solids': {
            'test': {
                'config': {
                    'run_config': databricks_run_config,
                    'databricks_host': HOST,
                    'databricks_token': TOKEN,
                }
            }
        }
    }
    result = execute_pipeline(test_pipe, config)
    assert result.success

    mock_submit_run.assert_called_once()
    task = databricks_run_config.pop('task')
    assert mock_submit_run.call_args[0][0] == databricks_run_config
    assert mock_submit_run.call_args[0][1] == task
    mock_wait_for_run.assert_called_once()
    assert mock_wait_for_run.call_args[0][1] == RUN_ID
