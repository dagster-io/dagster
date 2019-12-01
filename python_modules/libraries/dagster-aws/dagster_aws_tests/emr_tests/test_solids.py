from dagster_aws.emr.solids import EmrRunJobFlowSolidDefinition
from moto import mock_emr

from dagster import execute_pipeline, pipeline


@mock_emr
def test_run_emr_job(emr_cluster_config):
    @pipeline
    def test_pipe():
        EmrRunJobFlowSolidDefinition('test', max_wait_time_sec=2, poll_interval_sec=1)()

    config = {
        'solids': {
            'test': {'config': {'job_config': emr_cluster_config, 'aws_region': 'us-west-1'}}
        }
    }
    result = execute_pipeline(test_pipe, config)
    assert result.success
