import os
from unittest import mock

import pytest
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource
from dagster_azure.adls2 import adls2_pickle_io_manager, adls2_resource
from dagster_databricks import (
    DatabricksRunLifeCycleState,
    DatabricksRunResultState,
    databricks_pyspark_step_launcher,
)
from dagster_databricks.databricks import DatabricksRunState
from dagster_pyspark import DataFrame, pyspark_resource
from pyspark.sql import Row
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

from dagster import (
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    execute_pipeline,
    fs_io_manager,
    pipeline,
    reconstructable,
    solid,
)
from dagster.core.definitions.no_step_launcher import no_step_launcher
from dagster.core.test_utils import instance_for_test
from dagster.utils.merger import deep_merge_dicts

S3_BUCKET = "dagster-databricks-tests"
ADLS2_STORAGE_ACCOUNT = "dagsterdatabrickstests"
ADLS2_CONTAINER = "dagster-databricks-tests"


BASE_DATABRICKS_PYSPARK_STEP_LAUNCHER_CONFIG = {
    "databricks_host": os.environ.get("DATABRICKS_HOST"),
    "databricks_token": os.environ.get("DATABRICKS_TOKEN"),
    "local_pipeline_package_path": os.path.abspath(os.path.dirname(__file__)),
    "staging_prefix": "/dagster-databricks-tests",
    "run_config": {
        "cluster": {
            "new": {
                "size": {"num_workers": 1},
                "spark_version": "6.5.x-scala2.11",
                "nodes": {
                    "node_types": {"node_type_id": "Standard_DS3_v2"},
                },
            },
        },
        "libraries": [
            {"pypi": {"package": "azure-storage-file-datalake~=12.0.1"}},
            {"pypi": {"package": "dagster-aws"}},
            {"pypi": {"package": "dagster-azure"}},
            {"pypi": {"package": "databricks-api"}},
            {"pypi": {"package": "pytest"}},
        ],
    },
    "secrets_to_env_variables": [],
    "storage": {
        "s3": {
            "secret_scope": "dagster-databricks-tests",
            "access_key_key": "aws-access-key",
            "secret_key_key": "aws-secret-key",
        }
    },
}


@solid(
    output_defs=[OutputDefinition(DataFrame)],
    required_resource_keys={"pyspark_step_launcher", "pyspark"},
)
def make_df_solid(context):
    schema = StructType([StructField("name", StringType()), StructField("age", IntegerType())])
    rows = [Row(name="John", age=19), Row(name="Jennifer", age=29), Row(name="Henry", age=50)]
    return context.resources.pyspark.spark_session.createDataFrame(rows, schema)


@solid(
    name="blah",
    description="this is a test",
    config_schema={"foo": str, "bar": int},
    input_defs=[InputDefinition("people", DataFrame)],
    output_defs=[OutputDefinition(DataFrame)],
    required_resource_keys={"pyspark_step_launcher"},
)
def filter_df_solid(_, people):
    return people.filter(people["age"] < 30)


MODE_DEFS = [
    ModeDefinition(
        "prod_adls2",
        resource_defs={
            "pyspark_step_launcher": databricks_pyspark_step_launcher,
            "pyspark": pyspark_resource,
            "adls2": adls2_resource,
            "io_manager": adls2_pickle_io_manager,
        },
    ),
    ModeDefinition(
        "prod_s3",
        resource_defs={
            "pyspark_step_launcher": databricks_pyspark_step_launcher,
            "pyspark": pyspark_resource,
            "s3": s3_resource,
            "io_manager": s3_pickle_io_manager,
        },
    ),
    ModeDefinition(
        "test",
        resource_defs={
            "pyspark_step_launcher": databricks_pyspark_step_launcher,
            "pyspark": pyspark_resource,
            "io_manager": fs_io_manager,
        },
    ),
    ModeDefinition(
        "local",
        resource_defs={"pyspark_step_launcher": no_step_launcher, "pyspark": pyspark_resource},
    ),
]


@pipeline(mode_defs=MODE_DEFS)
def pyspark_pipe():
    filter_df_solid(make_df_solid())


def define_pyspark_pipe():
    return pyspark_pipe


@solid(
    required_resource_keys={"pyspark_step_launcher", "pyspark"},
)
def do_nothing_solid(_):
    pass


@pipeline(mode_defs=MODE_DEFS)
def do_nothing_pipe():
    do_nothing_solid()


def define_do_nothing_pipe():
    return do_nothing_pipe


def test_local():
    result = execute_pipeline(
        pipeline=reconstructable(define_pyspark_pipe),
        mode="local",
        run_config={"solids": {"blah": {"config": {"foo": "a string", "bar": 123}}}},
    )
    assert result.success


@mock.patch("dagster_databricks.databricks.DatabricksClient.submit_run")
@mock.patch("dagster_databricks.databricks.DatabricksClient.read_file")
@mock.patch("dagster_databricks.databricks.DatabricksClient.put_file")
@mock.patch("dagster_databricks.DatabricksPySparkStepLauncher.get_step_events")
@mock.patch("dagster_databricks.databricks.DatabricksClient.get_run_state")
def test_pyspark_databricks(
    mock_get_run_state, mock_get_step_events, mock_put_file, mock_read_file, mock_submit_run
):
    mock_submit_run.return_value = 12345
    mock_read_file.return_value = "somefilecontents".encode()

    running_state = DatabricksRunState(DatabricksRunLifeCycleState.Running, None, "")
    final_state = DatabricksRunState(
        DatabricksRunLifeCycleState.Terminated, DatabricksRunResultState.Success, ""
    )
    mock_get_run_state.side_effect = [running_state] * 5 + [final_state]

    with instance_for_test() as instance:
        execute_pipeline(
            pipeline=reconstructable(define_do_nothing_pipe), mode="local", instance=instance
        )
        mock_get_step_events.return_value = [
            record.event_log_entry
            for record in instance.get_event_records()
            if record.event_log_entry.step_key == "do_nothing_solid"
        ]
    config = BASE_DATABRICKS_PYSPARK_STEP_LAUNCHER_CONFIG.copy()
    config.pop("local_pipeline_package_path")
    result = execute_pipeline(
        pipeline=reconstructable(define_do_nothing_pipe),
        mode="test",
        run_config={
            "resources": {
                "pyspark_step_launcher": {
                    "config": deep_merge_dicts(
                        config,
                        {
                            "databricks_host": "",
                            "databricks_token": "",
                            "poll_interval_sec": 0.1,
                            "local_dagster_job_package_path": os.path.abspath(
                                os.path.dirname(__file__)
                            ),
                        },
                    ),
                },
            },
        },
    )
    assert result.success
    assert mock_get_run_state.call_count == 6
    assert mock_get_step_events.call_count == 6
    assert mock_put_file.call_count == 4
    assert mock_read_file.call_count == 2
    assert mock_submit_run.call_count == 1


@pytest.mark.skipif(
    "DATABRICKS_TEST_DO_IT_LIVE_S3" not in os.environ,
    reason="This test is slow and requires a Databricks cluster; run only upon explicit request",
)
def test_do_it_live_databricks_s3():
    result = execute_pipeline(
        reconstructable(define_pyspark_pipe),
        mode="prod_s3",
        run_config={
            "solids": {"blah": {"config": {"foo": "a string", "bar": 123}}},
            "resources": {
                "pyspark_step_launcher": {"config": BASE_DATABRICKS_PYSPARK_STEP_LAUNCHER_CONFIG},
                "io_manager": {
                    "config": {"s3_bucket": "elementl-databricks", "s3_prefix": "dagster-test"}
                },
            },
        },
    )
    assert result.success


@pytest.mark.skipif(
    "DATABRICKS_TEST_DO_IT_LIVE_ADLS2" not in os.environ,
    reason="This test is slow and requires a Databricks cluster; run only upon explicit request",
)
def test_do_it_live_databricks_adls2():
    config = BASE_DATABRICKS_PYSPARK_STEP_LAUNCHER_CONFIG.copy()
    config["storage"] = {
        "adls2": {
            "secret_scope": "dagster-databricks-tests",
            "storage_account_name": ADLS2_STORAGE_ACCOUNT,
            "storage_account_key_key": "adls2-storage-key",
        }
    }

    result = execute_pipeline(
        reconstructable(define_pyspark_pipe),
        mode="prod_adls2",
        run_config={
            "solids": {"blah": {"config": {"foo": "a string", "bar": 123}}},
            "resources": {
                "pyspark_step_launcher": {"config": config},
                "adls2": {
                    "config": {
                        "storage_account": ADLS2_STORAGE_ACCOUNT,
                        "credential": {"key": os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")},
                    }
                },
                "io_manager": {
                    "config": {
                        "adls2_file_system": ADLS2_CONTAINER,
                        "adls2_prefix": "dagster-databricks-tests",
                    }
                },
            },
        },
    )
    assert result.success
