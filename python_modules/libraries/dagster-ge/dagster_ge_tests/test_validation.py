import pytest
from dagster import In, Output, graph, op
from dagster._core.definitions.metadata.metadata_value import MarkdownMetadataValue
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from dagster._utils import file_relative_path
from dagster_ge.factory import GEContextResource, ge_data_context, ge_validation_op_factory
from dagster_pyspark import (
    DataFrame as DagsterPySparkDataFrame,
    pyspark_resource,
)
from pandas import read_csv


@op(ins={"res": In()})
def unpack_ge_results(_context, res):
    yield Output((res["statistics"], res["results"]))


# ########################
# ##### PANDAS
# ########################


@op
def pandas_loader(_):
    return read_csv(file_relative_path(__file__, "./basic.csv"))


pandas_validator = ge_validation_op_factory(
    name="ge_validation_op",
    datasource_name="getest",
    data_connector_name="my_runtime_data_connector",
    data_asset_name="test_asset",
    suite_name="basic.warning",
    batch_identifiers={"foo": "bar"},
)


@graph
def pandas_graph():
    unpack_ge_results(pandas_validator(pandas_loader()))


pandas_job_with_resource = pandas_graph.to_job(resource_defs={"ge_data_context": ge_data_context})

pandas_job_no_resource = pandas_graph.to_job()

# ########################
# ##### PYSPARK
# ########################


@op(required_resource_keys={"pyspark"})
def pyspark_loader(context: OpExecutionContext):
    return (
        context.resources.pyspark.spark_session.read.format("csv")
        .options(header="true", inferSchema="true")
        .load(file_relative_path(__file__, "./basic.csv"))
    )


pyspark_validator = ge_validation_op_factory(
    name="ge_validation_op",
    datasource_name="getestspark",
    data_connector_name="my_runtime_data_connector",
    data_asset_name="test_asset",
    suite_name="basic.warning",
    input_dagster_type=DagsterPySparkDataFrame,
    batch_identifiers={"foo": "bar"},
)


@graph
def pyspark_graph():
    return unpack_ge_results(pyspark_validator(pyspark_loader()))


pyspark_job_with_resource = pyspark_graph.to_job(
    resource_defs={
        "ge_data_context": ge_data_context,
        "pyspark": pyspark_resource,
    }
)

pyspark_job_no_resource = pyspark_graph.to_job()

# ########################
# ##### TESTS
# ########################

_GE_ROOT_DIR = file_relative_path(__file__, "./gx")


@pytest.mark.parametrize(
    "data_backend, resource_style",
    [
        ("pandas", "new"),
        ("pandas", "old"),
        ("pyspark", "new"),
        ("pyspark", "old"),
    ],
)
def test_ge_validation(snapshot, data_backend: str, resource_style: str):
    # Used for old resource style
    run_config = {"resources": {"ge_data_context": {"config": {"ge_root_dir": _GE_ROOT_DIR}}}}

    # Used for new resource style
    ge_resource = GEContextResource(ge_root_dir=_GE_ROOT_DIR)

    # Compute result based on data backend and resource style. When resource_style=old, resources
    # are set on the job and are configured via the passed run_config. When resource_style=new,
    # resources are passed directly into `execute_in_process`.
    if data_backend == "pandas" and resource_style == "new":
        result = pandas_job_no_resource.execute_in_process(
            resources={
                "ge_data_context": ge_resource,
            },
        )
    elif data_backend == "pandas" and resource_style == "old":
        result = pandas_job_with_resource.execute_in_process(run_config=run_config)
    elif data_backend == "pyspark" and resource_style == "new":
        result = pyspark_job_no_resource.execute_in_process(
            resources={
                "ge_data_context": ge_resource,
                "pyspark": pyspark_resource,
            },
        )
    elif data_backend == "pyspark" and resource_style == "old":
        result = pyspark_job_with_resource.execute_in_process(run_config=run_config)
    else:
        raise ValueError("Invalid combination")

    assert result.output_for_node("unpack_ge_results")[0]["success_percent"] == 100
    expectations = result.expectation_results_for_node("ge_validation_op")
    assert len(expectations) == 1
    mainexpect = expectations[0]
    assert mainexpect.success
    # purge system specific metadata for testing
    result_markdown_metadata = mainexpect.metadata["Expectation Results"]
    assert (
        isinstance(result_markdown_metadata, MarkdownMetadataValue)
        and result_markdown_metadata.md_str
    )
    result_markdown = result_markdown_metadata.md_str.split("### Info")[0]
    snapshot.assert_match(result_markdown)
