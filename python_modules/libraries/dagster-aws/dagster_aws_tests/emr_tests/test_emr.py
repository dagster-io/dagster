import pytest

from moto import mock_emr

from dagster import execute_pipeline, PipelineDefinition
from dagster_aws.emr.solids import EmrRunJobFlowSolidDefinition


@pytest.mark.skip
@mock_emr
def test_run_emr_job():
    e = EmrRunJobFlowSolidDefinition('test')
    pipeline = PipelineDefinition(name='test', solid_defs=[e])
    emr_config = {
        'Name': 'test-pyspark',
        'ReleaseLabel': 'emr-5.23.0',
        'Instances': {
            'MasterInstanceType': 'm4.large',
            'SlaveInstanceType': 'm4.large',
            'InstanceCount': 4,
            'TerminationProtected': False,
        },
        'Applications': [{'Name': 'Spark'}],
        'BootstrapActions': [
            {
                'Name': 'Spark Default Config',
                'ScriptBootstrapAction': {
                    'Path': 's3://support.elasticmapreduce/spark/maximize-spark-default-config'
                },
            }
        ],
        'Steps': [
            {
                'Name': 'Setup Debugging',
                'ActionOnFailure': 'TERMINATE_CLUSTER',
                'HadoopJarStep': {'Jar': 'command-runner.jar', 'Args': ['state-pusher-script']},
            },
            {
                'Name': 'setup - copy files',
                'ActionOnFailure': 'TERMINATE_CLUSTER',
                'HadoopJarStep': {
                    'Jar': 'command-runner.jar',
                    'Args': [
                        'aws',
                        's3',
                        'cp',
                        's3://elementl-public/pyspark/hello_world.py',
                        '/home/hadoop/',
                    ],
                },
            },
            {
                'Name': 'Run Spark',
                'ActionOnFailure': 'TERMINATE_CLUSTER',
                'HadoopJarStep': {
                    'Jar': 'command-runner.jar',
                    'Args': ['spark-submit', '/home/hadoop/main.py'],
                },
            },
        ],
        'VisibleToAllUsers': True,
        'JobFlowRole': 'EMR_EC2_DefaultRole',
        'ServiceRole': 'EMR_DefaultRole',
    }
    config = {'solids': {'test': {'config': {'job_config': emr_config, 'aws_region': 'us-east-1'}}}}
    result = execute_pipeline(pipeline, config)
    assert result.success
