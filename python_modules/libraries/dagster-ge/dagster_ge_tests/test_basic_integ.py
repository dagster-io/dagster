from dagster import (
    InputDefinition,
    ModeDefinition,
    Output,
    execute_pipeline,
    pipeline,
    reconstructable,
    solid,
)
from dagster.core.test_utils import instance_for_test
from dagster.utils import file_relative_path
from dagster_ge.factory import ge_data_context, ge_validation_solid_factory
from dagster_pyspark import DataFrame as DagsterPySparkDataFrame
from dagster_pyspark import pyspark_resource
from pandas import read_csv


@solid
def pandas_yielder(_):
    return read_csv(file_relative_path(__file__, "./basic.csv"))


@solid(required_resource_keys={"pyspark"})
def pyspark_yielder(context):
    return (
        context.resources.pyspark.spark_session.read.format("csv")
        .options(header="true", inferSchema="true")
        .load(file_relative_path(__file__, "./basic.csv"))
    )


@solid(input_defs=[InputDefinition(name="res")])
def reyielder(_context, res):
    yield Output((res["statistics"], res["results"]))


@pipeline(
    mode_defs=[ModeDefinition("basic", resource_defs={"ge_data_context": ge_data_context})],
)
def hello_world_pandas_pipeline():
    return reyielder(
        ge_validation_solid_factory("ge_validation_solid", "getest", "basic.warning")(
            pandas_yielder()
        )
    )


@pipeline(
    mode_defs=[
        ModeDefinition(
            "basic", resource_defs={"ge_data_context": ge_data_context, "pyspark": pyspark_resource}
        )
    ],
)
def hello_world_pyspark_pipeline():
    validate = ge_validation_solid_factory(
        "ge_validation_solid",
        "getestspark",
        "basic.warning",
        input_dagster_type=DagsterPySparkDataFrame,
    )
    return reyielder(validate(pyspark_yielder()))


def test_yielded_results_config_pandas(snapshot):
    run_config = {
        "resources": {
            "ge_data_context": {
                "config": {"ge_root_dir": file_relative_path(__file__, "./great_expectations")}
            }
        }
    }
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(hello_world_pandas_pipeline),
            run_config=run_config,
            mode="basic",
            instance=instance,
        )
        assert result.result_for_solid("reyielder").output_value()[0]["success_percent"] == 100
        expectations = result.result_for_solid(
            "ge_validation_solid"
        ).expectation_results_during_compute
        assert len(expectations) == 1
        mainexpect = expectations[0]
        assert mainexpect.success
        # purge system specific metadata for testing
        metadata = mainexpect.metadata_entries[0].entry_data.md_str.split("### Info")[0]
        snapshot.assert_match(metadata)


def test_yielded_results_config_pyspark(snapshot):  # pylint:disable=unused-argument
    run_config = {
        "resources": {
            "ge_data_context": {
                "config": {"ge_root_dir": file_relative_path(__file__, "./great_expectations")}
            }
        }
    }
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(hello_world_pyspark_pipeline),
            run_config=run_config,
            mode="basic",
            instance=instance,
        )
        assert result.result_for_solid("reyielder").output_value()[0]["success_percent"] == 100
        expectations = result.result_for_solid(
            "ge_validation_solid"
        ).expectation_results_during_compute
        assert len(expectations) == 1
        mainexpect = expectations[0]
        assert mainexpect.success
