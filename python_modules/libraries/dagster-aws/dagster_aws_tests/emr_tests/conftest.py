import pytest


@pytest.fixture(scope='session')
def emr_cluster_config():
    return {
        'Name': 'test-emr',
        'LogUri': 's3n://emr-cluster-logs/elasticmapreduce/',
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
        ],
        'VisibleToAllUsers': True,
        'JobFlowRole': 'EMR_EC2_DefaultRole',
        'ServiceRole': 'EMR_DefaultRole',
    }
