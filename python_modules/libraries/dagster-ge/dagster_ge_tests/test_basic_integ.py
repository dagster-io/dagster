# pylint: disable=no-value-for-parameter

import pytest
from dagster_ge.factory import (
    ge_data_context,
    ge_validation_op_factory,
    ge_validation_op_factory_v3,
)
from dagster_pyspark import DataFrame as DagsterPySparkDataFrame
from dagster_pyspark import pyspark_resource
from pandas import read_csv

from dagster import In, Output, job, op
from dagster._utils import file_relative_path


@op
def pandas_yielder(_):
    return read_csv(file_relative_path(__file__, "./basic.csv"))


@op(required_resource_keys={"pyspark"})
def pyspark_yielder(context):
    return (
        context.resources.pyspark.spark_session.read.format("csv")
        .options(header="true", inferSchema="true")
        .load(file_relative_path(__file__, "./basic.csv"))
    )


@op(ins={"res": In()})
def reyielder(_context, res):
    yield Output((res["statistics"], res["results"]))


@job(resource_defs={"ge_data_context": ge_data_context})
def hello_world_pandas_job_v2():
    reyielder(
        ge_validation_op_factory("ge_validation_op", "getest", "basic.warning")(pandas_yielder())
    )


@job(resource_defs={"ge_data_context": ge_data_context})
def hello_world_pandas_job_v3():
    reyielder(
        ge_validation_op_factory_v3(
            name="ge_validation_op",
            datasource_name="getest",
            data_connector_name="my_runtime_data_connector",
            data_asset_name="test_asset",
            suite_name="basic.warning",
            batch_identifiers={"foo": "bar"},
        )(pandas_yielder())
    )


@job(
    resource_defs={
        "ge_data_context": ge_data_context,
        "pyspark": pyspark_resource,
    }
)
def hello_world_pyspark_job():
    validate = ge_validation_op_factory(
        "ge_validation_op",
        "getestspark",
        "basic.warning",
        input_dagster_type=DagsterPySparkDataFrame,
    )
    reyielder(validate(pyspark_yielder()))


@pytest.mark.parametrize(
    "job_def, ge_dir",
    [
        (hello_world_pandas_job_v2, "./great_expectations"),
        (hello_world_pandas_job_v3, "./great_expectations_v3"),
    ],
)
def test_yielded_results_config_pandas(snapshot, job_def, ge_dir):
    run_config = {
        "resources": {
            "ge_data_context": {"config": {"ge_root_dir": file_relative_path(__file__, ge_dir)}}
        }
    }
    result = job_def.execute_in_process(run_config=run_config)
    assert result.output_for_node("reyielder")[0]["success_percent"] == 100
    expectations = result.expectation_results_for_node("ge_validation_op")
    assert len(expectations) == 1
    mainexpect = expectations[0]
    assert mainexpect.success
    # purge system specific metadata for testing
    metadata = mainexpect.metadata_entries[0].entry_data.md_str.split("### Info")[0]
    snapshot.assert_match(metadata)


def test_yielded_results_config_pyspark_v2(snapshot):  # pylint:disable=unused-argument
    run_config = {
        "resources": {
            "ge_data_context": {
                "config": {"ge_root_dir": file_relative_path(__file__, "./great_expectations")}
            }
        }
    }
    result = hello_world_pyspark_job.execute_in_process(run_config=run_config)
    assert result.output_for_node("reyielder")[0]["success_percent"] == 100
    expectations = result.expectation_results_for_node("ge_validation_op")
    assert len(expectations) == 1
    mainexpect = expectations[0]
    assert mainexpect.success
    # purge system specific metadata for testing
    metadata = mainexpect.metadata_entries[0].entry_data.md_str.split("### Info")[0]
    snapshot.assert_match(metadata)
