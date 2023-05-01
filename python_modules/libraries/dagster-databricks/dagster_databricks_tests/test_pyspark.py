import os
from typing import Dict
from unittest import mock

import pytest
from dagster import In, Out, execute_job, fs_io_manager, graph, op, reconstructable
from dagster._core.definitions.no_step_launcher import no_step_launcher
from dagster._core.test_utils import instance_for_test
from dagster._utils.merger import deep_merge_dicts
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource
from dagster_azure.adls2 import adls2_pickle_io_manager, adls2_resource
from dagster_databricks import (
    databricks_pyspark_step_launcher,
)
from dagster_databricks.types import (
    DatabricksRunLifeCycleState,
    DatabricksRunResultState,
    DatabricksRunState,
)
from dagster_pyspark import DataFrame, pyspark_resource
from pyspark.sql import Row
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

S3_BUCKET = "dagster-databricks-tests"
ADLS2_STORAGE_ACCOUNT = "dagsterdatabrickstests"
ADLS2_CONTAINER = "dagster-databricks-tests"


BASE_DATABRICKS_PYSPARK_STEP_LAUNCHER_CONFIG: Dict[str, object] = {
    "databricks_host": os.environ.get("DATABRICKS_HOST") or "https://",
    "databricks_token": os.environ.get("DATABRICKS_TOKEN"),
    "local_job_package_path": os.path.abspath(os.path.dirname(__file__)),
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
    "permissions": {
        "cluster_permissions": {"CAN_MANAGE": [{"group_name": "my_group"}]},
        "job_permissions": {"CAN_MANAGE_RUN": [{"user_name": "my_user"}]},
    },
    "secrets_to_env_variables": [],
    "env_variables": {},
    "storage": {
        "s3": {
            "secret_scope": "dagster-databricks-tests",
            "access_key_key": "aws-access-key",
            "secret_key_key": "aws-secret-key",
        }
    },
}


@op(
    out=Out(dagster_type=DataFrame),
    required_resource_keys={"pyspark_step_launcher", "pyspark"},
)
def make_df_op(context):
    schema = StructType([StructField("name", StringType()), StructField("age", IntegerType())])
    rows = [
        Row(name="John", age=19),
        Row(name="Jennifer", age=29),
        Row(name="Henry", age=50),
    ]
    return context.resources.pyspark.spark_session.createDataFrame(rows, schema)


@op(
    name="blah",
    description="this is a test",
    config_schema={"foo": str, "bar": int},
    ins={"people": In(dagster_type=DataFrame)},
    out=Out(dagster_type=DataFrame),
    required_resource_keys={"pyspark_step_launcher"},
)
def filter_df_op(_, people):
    return people.filter(people["age"] < 30)


ADLS2_RESOURCE_DEFS = {
    "pyspark_step_launcher": databricks_pyspark_step_launcher,
    "pyspark": pyspark_resource,
    "adls2": adls2_resource,
    "io_manager": adls2_pickle_io_manager,
}
S3_RESOURCE_DEFS = {
    "pyspark_step_launcher": databricks_pyspark_step_launcher,
    "pyspark": pyspark_resource,
    "s3": s3_resource,
    "io_manager": s3_pickle_io_manager,
}
TEST_RESOURCE_DEFS = {
    "pyspark_step_launcher": databricks_pyspark_step_launcher,
    "pyspark": pyspark_resource,
    "io_manager": fs_io_manager,
}
LOCAL_RESOURCE_DEFS = {
    "pyspark_step_launcher": no_step_launcher,
    "pyspark": pyspark_resource,
}


@graph
def pyspark_graph():
    filter_df_op(make_df_op())


pyspark_local_job = pyspark_graph.to_job(resource_defs=LOCAL_RESOURCE_DEFS)
pyspark_s3_job = pyspark_graph.to_job(resource_defs=S3_RESOURCE_DEFS)
pyspark_adls2_job = pyspark_graph.to_job(resource_defs=ADLS2_RESOURCE_DEFS)


def define_pyspark_local_job():
    return pyspark_local_job


def define_pyspark_s3_job():
    return pyspark_s3_job


def define_pyspark_adls2_job():
    return pyspark_adls2_job


@op(
    required_resource_keys={"pyspark_step_launcher", "pyspark"},
)
def do_nothing_op(_):
    pass


@graph
def do_nothing_graph():
    do_nothing_op()


do_nothing_local_job = do_nothing_graph.to_job(resource_defs=LOCAL_RESOURCE_DEFS)
do_nothing_test_job = do_nothing_graph.to_job(resource_defs=TEST_RESOURCE_DEFS)


def define_do_nothing_test_job():
    return do_nothing_test_job


def test_local():
    result = pyspark_local_job.execute_in_process(
        run_config={
            "ops": {
                "blah": {"config": {"foo": "a string", "bar": 123}},
            }
        }
    )
    assert result.success


@mock.patch("databricks_cli.sdk.JobsService.submit_run")
@mock.patch("dagster_databricks.databricks.DatabricksClient.read_file")
@mock.patch("dagster_databricks.databricks.DatabricksClient.put_file")
@mock.patch("dagster_databricks.DatabricksPySparkStepLauncher.get_step_events")
@mock.patch("databricks_cli.sdk.JobsService.get_run")
@mock.patch("dagster_databricks.databricks.DatabricksClient.get_run_state")
@mock.patch("databricks_cli.sdk.api_client.ApiClient.perform_query")
def test_pyspark_databricks(
    mock_perform_query,
    mock_get_run_state,
    mock_get_run,
    mock_get_step_events,
    mock_put_file,
    mock_read_file,
    mock_submit_run,
):
    mock_submit_run.return_value = {"run_id": 12345}
    mock_read_file.return_value = "somefilecontents".encode()

    running_state = DatabricksRunState(DatabricksRunLifeCycleState.RUNNING, None, "")
    final_state = DatabricksRunState(
        DatabricksRunLifeCycleState.TERMINATED, DatabricksRunResultState.SUCCESS, ""
    )
    mock_get_run_state.side_effect = [running_state] * 5 + [final_state]

    with instance_for_test() as instance:
        result = do_nothing_local_job.execute_in_process(instance=instance)
        mock_get_step_events.return_value = [
            event for event in instance.all_logs(result.run_id) if event.step_key == "do_nothing_op"
        ]

    # Test 1 - successful execution

    with instance_for_test() as instance:
        config = BASE_DATABRICKS_PYSPARK_STEP_LAUNCHER_CONFIG.copy()
        config.pop("local_job_package_path")
        result = execute_job(
            job=reconstructable(define_do_nothing_test_job),
            instance=instance,
            run_config={
                "resources": {
                    "pyspark_step_launcher": {
                        "config": deep_merge_dicts(
                            config,
                            {
                                "databricks_host": "https://",
                                "databricks_token": "",
                                "poll_interval_sec": 0.1,
                                "local_dagster_job_package_path": os.path.abspath(
                                    os.path.dirname(__file__)
                                ),
                            },
                        ),
                    },
                },
                "execution": {"config": {"in_process": {}}},
            },
        )
        assert result.success
        assert mock_perform_query.call_count == 2
        assert mock_get_run.call_count == 1
        assert mock_get_run_state.call_count == 6
        assert mock_get_step_events.call_count == 6
        assert mock_put_file.call_count == 4
        assert mock_read_file.call_count == 2
        assert mock_submit_run.call_count == 1

    # Test 2 - attempting to update permissions for an existing cluster

    with instance_for_test() as instance:
        config = BASE_DATABRICKS_PYSPARK_STEP_LAUNCHER_CONFIG.copy()
        config.pop("local_job_package_path")
        config["run_config"]["cluster"] = {"existing": "cluster_id"}
        with pytest.raises(ValueError) as excinfo:
            execute_job(
                job=reconstructable(define_do_nothing_test_job),
                instance=instance,
                run_config={
                    "resources": {
                        "pyspark_step_launcher": {
                            "config": deep_merge_dicts(
                                config,
                                {
                                    "databricks_host": "https://",
                                    "databricks_token": "",
                                    "poll_interval_sec": 0.1,
                                    "local_dagster_job_package_path": os.path.abspath(
                                        os.path.dirname(__file__)
                                    ),
                                },
                            ),
                        },
                    },
                    "execution": {"config": {"in_process": {}}},
                },
                raise_on_error=True,
            )

        assert (
            str(excinfo.value)
            == "Attempting to update permissions of an existing cluster. This is dangerous and"
            " thus unsupported."
        )


@pytest.mark.skipif(
    "DATABRICKS_TEST_DO_IT_LIVE_S3" not in os.environ,
    reason="This test is slow and requires a Databricks cluster; run only upon explicit request",
)
def test_do_it_live_databricks_s3():
    result = execute_job(
        reconstructable(define_pyspark_s3_job),
        run_config={
            "ops": {"blah": {"config": {"foo": "a string", "bar": 123}}},
            "resources": {
                "pyspark_step_launcher": {"config": BASE_DATABRICKS_PYSPARK_STEP_LAUNCHER_CONFIG},
                "io_manager": {
                    "config": {
                        "s3_bucket": "elementl-databricks",
                        "s3_prefix": "dagster-test",
                    }
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

    result = execute_job(
        reconstructable(define_pyspark_adls2_job),
        run_config={
            "ops": {"blah": {"config": {"foo": "a string", "bar": 123}}},
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
