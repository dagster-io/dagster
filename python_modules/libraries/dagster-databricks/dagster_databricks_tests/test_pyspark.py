import os

import pytest
from dagster import (
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    execute_pipeline,
    pipeline,
    reconstructable,
    solid,
)
from dagster.core.definitions.no_step_launcher import no_step_launcher
from dagster.seven import mock
from dagster.utils.merger import deep_merge_dicts
from dagster_aws.s3 import s3_plus_default_intermediate_storage_defs, s3_resource
from dagster_azure.adls2 import adls2_plus_default_intermediate_storage_defs, adls2_resource
from dagster_databricks import databricks_pyspark_step_launcher
from dagster_pyspark import DataFrame, pyspark_resource
from pyspark.sql import Row
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

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
                "nodes": {"node_types": {"node_type_id": "Standard_DS3_v2"},},
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
        },
        intermediate_storage_defs=adls2_plus_default_intermediate_storage_defs,
    ),
    ModeDefinition(
        "prod_s3",
        resource_defs={
            "pyspark_step_launcher": databricks_pyspark_step_launcher,
            "pyspark": pyspark_resource,
            "s3": s3_resource,
        },
        intermediate_storage_defs=s3_plus_default_intermediate_storage_defs,
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


@solid(required_resource_keys={"pyspark_step_launcher", "pyspark"},)
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
@mock.patch("dagster_databricks.databricks.DatabricksClient.put_file")
@mock.patch("dagster_databricks.DatabricksPySparkStepLauncher.get_step_events")
@mock.patch("dagster_databricks.databricks.DatabricksJobRunner.wait_for_run_to_complete")
def test_pyspark_databricks(mock_wait, mock_get_step_events, mock_put_file, mock_submit_run):
    mock_get_step_events.return_value = execute_pipeline(
        pipeline=reconstructable(define_do_nothing_pipe), mode="local"
    ).events_by_step_key["do_nothing_solid"]

    result = execute_pipeline(
        pipeline=reconstructable(define_do_nothing_pipe),
        mode="prod_s3",
        run_config={
            "resources": {
                "pyspark_step_launcher": {
                    "config": deep_merge_dicts(
                        BASE_DATABRICKS_PYSPARK_STEP_LAUNCHER_CONFIG,
                        {"databricks_host": "", "databricks_token": ""},
                    ),
                },
            },
        },
    )
    assert result.success
    assert mock_wait.call_count == 1
    assert mock_get_step_events.call_count == 1
    assert mock_put_file.call_count == 4
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
            },
            "intermediate_storage": {
                "s3": {
                    "config": {
                        "s3_bucket": "dagster-databricks-tests",
                        "s3_prefix": "dagster-databricks-tests",
                    }
                }
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
            },
            "intermediate_storage": {
                "adls2": {
                    "config": {
                        "adls2_file_system": ADLS2_CONTAINER,
                        "adls2_prefix": "dagster-databricks-tests",
                    }
                }
            },
        },
    )
    assert result.success
