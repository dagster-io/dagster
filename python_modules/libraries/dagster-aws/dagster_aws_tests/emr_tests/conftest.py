import pytest


@pytest.fixture
def emr_cluster_config(mock_s3_bucket):
    return {
        "Name": "test-emr",
        "LogUri": "s3n://{bucket}/elasticmapreduce/".format(bucket=mock_s3_bucket.name),
        "ReleaseLabel": "emr-5.23.0",
        "Instances": {
            "MasterInstanceType": "m4.large",
            "SlaveInstanceType": "m4.large",
            "InstanceCount": 4,
            "TerminationProtected": False,
        },
        "Applications": [{"Name": "Spark"}],
        "BootstrapActions": [
            {
                "Name": "Spark Default Config",
                "ScriptBootstrapAction": {
                    "Path": "s3://support.elasticmapreduce/spark/maximize-spark-default-config"
                },
            }
        ],
        "Steps": [
            {
                "Name": "Setup Debugging",
                "ActionOnFailure": "TERMINATE_CLUSTER",
                "HadoopJarStep": {"Jar": "command-runner.jar", "Args": ["state-pusher-script"]},
            },
        ],
        "VisibleToAllUsers": True,
        "JobFlowRole": "EMR_EC2_DefaultRole",
        "ServiceRole": "EMR_DefaultRole",
    }
