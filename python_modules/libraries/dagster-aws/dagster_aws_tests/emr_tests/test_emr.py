from dagster_aws.emr import EmrClusterState, EmrJobRunner
from moto import mock_emr

from dagster.utils.test import create_test_pipeline_execution_context

REGION = 'us-west-1'


@mock_emr
def test_emr_create_cluster(emr_cluster_config):
    context = create_test_pipeline_execution_context()
    cluster = EmrJobRunner(region=REGION)
    cluster_id = cluster.run_job_flow(context, emr_cluster_config)
    assert cluster_id.startswith('j-')


@mock_emr
def test_emr_describe_cluster(emr_cluster_config):
    context = create_test_pipeline_execution_context()
    cluster = EmrJobRunner(region=REGION)
    cluster_id = cluster.run_job_flow(context, emr_cluster_config)
    cluster_info = cluster.describe_cluster(cluster_id)
    assert cluster_info['Name'] == 'test-emr'
    assert EmrClusterState(cluster_info['Status']['State']) == EmrClusterState.Waiting
