import pytest
from dagster import Output, job, op
from dagster._utils import file_relative_path
from dagster_ge.factory import (
    GEContextResource,
    ge_validation_op_factory,
    ge_validation_op_factory_v3,
)
from pandas import read_csv


@op
def pandas_yielder(_):
    return read_csv(file_relative_path(__file__, "./basic.csv"))


@op
def reyielder(_context, res):
    yield Output((res["statistics"], res["results"]))


@job
def hello_world_pandas_job_v2():
    reyielder(
        ge_validation_op_factory("ge_validation_op", "getest", "basic.warning")(pandas_yielder())
    )


@job
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


@pytest.mark.parametrize(
    "job_def, ge_dir",
    [
        (hello_world_pandas_job_v2, "./great_expectations"),
        (hello_world_pandas_job_v3, "./great_expectations_v3"),
    ],
)
def test_yielded_results_config_pandas(snapshot, job_def, ge_dir):
    result = job_def.execute_in_process(
        resources={
            "ge_data_context": GEContextResource(ge_root_dir=file_relative_path(__file__, ge_dir))
        },
    )
    assert result.output_for_node("reyielder")[0]["success_percent"] == 100
    expectations = result.expectation_results_for_node("ge_validation_op")
    assert len(expectations) == 1
    mainexpect = expectations[0]
    assert mainexpect.success
    # purge system specific metadata for testing
    metadata = mainexpect.metadata["Expectation Results"].md_str.split("### Info")[0]
    snapshot.assert_match(metadata)
