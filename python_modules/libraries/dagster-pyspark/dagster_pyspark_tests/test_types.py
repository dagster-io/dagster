import pytest
from dagster import file_relative_path
from dagster._core.definitions.decorators import op
from dagster._core.definitions.input import In
from dagster._utils import dict_without_keys
from dagster._utils.test import wrap_op_in_graph_and_execute
from dagster_pyspark import (
    DataFrame as DagsterPySparkDataFrame,
    lazy_pyspark_resource,
    pyspark_resource,
)
from pyspark.sql import Row, SparkSession

spark = SparkSession.builder.getOrCreate()  # type: ignore

dataframe_parametrize_argnames = "file_type,read,other,resource"
dataframe_parametrize_argvalues = [
    pytest.param("csv", spark.read.csv, False, pyspark_resource, id="csv"),
    pytest.param("parquet", spark.read.parquet, False, pyspark_resource, id="parquet"),
    pytest.param("json", spark.read.json, False, pyspark_resource, id="json"),
    pytest.param("csv", spark.read.load, True, pyspark_resource, id="other_csv"),
    pytest.param("parquet", spark.read.load, True, pyspark_resource, id="other_parquet"),
    pytest.param("json", spark.read.load, True, pyspark_resource, id="other_json"),
    pytest.param("csv", spark.read.csv, False, lazy_pyspark_resource, id="csv"),
    pytest.param("parquet", spark.read.parquet, False, lazy_pyspark_resource, id="lazy_parquet"),
    pytest.param("json", spark.read.json, False, lazy_pyspark_resource, id="lazy_json"),
    pytest.param("csv", spark.read.load, True, lazy_pyspark_resource, id="lazy_other_csv_lazy"),
    pytest.param("parquet", spark.read.load, True, lazy_pyspark_resource, id="lazy_other_parquet"),
    pytest.param("json", spark.read.load, True, lazy_pyspark_resource, id="lazy_other_json"),
]


def create_pyspark_df():
    data = [Row(_c0=str(i), _c1=str(i)) for i in range(100)]
    return spark.createDataFrame(data)


@pytest.mark.parametrize(dataframe_parametrize_argnames, dataframe_parametrize_argvalues)
def test_dataframe_inputs(file_type, read, other, resource):
    @op(
        ins={"input_df": In(DagsterPySparkDataFrame)},
    )
    def return_df(_, input_df):
        return input_df

    options = {"path": file_relative_path(__file__, f"num.{file_type}")}
    if other:
        options["format"] = file_type
        file_type = "other"

    result = wrap_op_in_graph_and_execute(
        return_df,
        resources={"pyspark": resource},
        run_config={"ops": {"return_df": {"inputs": {"input_df": {file_type: options}}}}},
        do_input_mapping=False,
    )
    assert result.success
    actual = read(options["path"], **dict_without_keys(options, "path"))
    assert sorted(result.output_value().collect()) == sorted(actual.collect())
