import re

import pandera.polars as pa
import pandera.typing as pa_typing
import polars as pl
import pytest
from dagster import DagsterType, Out, TypeCheck, asset, check_dagster_type, job, materialize, op
from dagster._core.definitions.metadata import TableSchemaMetadataValue
from dagster._core.definitions.metadata.table import (
    TableColumn,
    TableColumnConstraints,
    TableConstraints,
    TableSchema,
)
from dagster_pandera import pandera_schema_to_dagster_type
from pandera.api.pandas.model_config import BaseConfig

# ########################
# ##### FIXTURES
# ########################

# ----- DATAFRAME

DATA_OK = {
    "a": [1, 4, 0, 10, 9],
    "b": [-1.3, -1.4, -2.9, -10.1, -20.4],
    "c": ["value_1", "value_2", "value_3", "value_2", "value_1"],
}


@pytest.fixture
def dataframe():
    return pl.DataFrame(DATA_OK)


# ----- SCHEMA


def sample_dataframe_schema(**kwargs):
    return pa.DataFrameSchema(
        {
            "a": pa.Column(int, checks=pa.Check.le(10), description="a desc"),
            "b": pa.Column(float, checks=pa.Check.lt(-1.2), description="b desc"),
            "c": pa.Column(
                str,
                description="c desc",
                checks=[
                    pa.Check.str_startswith("value_"),
                    pa.Check(
                        lambda s: s.str.split("_", expand=True).shape[1] == 2,
                        description="Two words separated by underscore.",
                    ),
                ],
            ),
        },
        checks=[
            pa.Check(lambda df: df["a"].sum() > df["b"].sum(), description="sum(a) > sum(b)."),
        ],
        **kwargs,
    )


def make_schema_model_config(**config_attrs):
    class Config(BaseConfig):
        pass

    for k, v in config_attrs.items():
        setattr(Config, k, v)
    return Config


def sample_schema_model(**config_attrs):
    class SampleDataframeModel(pa.DataFrameModel):
        a: pa_typing.Series[int] = pa.Field(le=10, description="a desc")
        b: pa_typing.Series[float] = pa.Field(lt=-1.2, description="b desc")
        c: pa_typing.Series[str] = pa.Field(str_startswith="value_", description="c desc")

        @pa.check("c")
        def c_check(cls, series: pa_typing.Series[str]) -> pa_typing.Series[bool]:
            """Two words separated by underscore."""
            split_df = series.lazyframe.select(pl.col(series.key).str.split("_", inclusive=True))
            return split_df.select(pl.col(series.key).list.len() == 2)

        @pa.dataframe_check
        def a_gt_b(cls, df):
            """sum(a) > sum(b)."""
            sum_a = df.lazyframe.select(pl.col("a")).sum().collect().item()
            sum_b = df.lazyframe.select(pl.col("b")).sum().collect().item()
            return sum_a > sum_b

        Config = make_schema_model_config(**config_attrs)  # pyright: ignore[reportAssignmentType]

    return SampleDataframeModel


@pytest.fixture(
    params=[sample_dataframe_schema, sample_schema_model], ids=["regular_schema", "schema_model"]
)
def schema(request):
    return request.param()


# ----- DAGSTER TYPE


@pytest.fixture
def dagster_type():
    return pandera_schema_to_dagster_type(sample_schema_model())


# ########################
# ##### TESTS
# ########################

# ----- TYPE CONSTRUCTION


def test_pandera_schema_to_dagster_type(schema):
    dagster_type = pandera_schema_to_dagster_type(schema)
    assert isinstance(dagster_type, DagsterType)
    assert len(dagster_type.metadata) == 1
    schema_metadata = dagster_type.metadata["schema"]
    assert isinstance(schema_metadata, TableSchemaMetadataValue)
    assert schema_metadata.schema == TableSchema(
        constraints=TableConstraints(other=["sum(a) > sum(b)."]),
        columns=[
            TableColumn(
                name="a",
                type="Int64",
                description="a desc",
                constraints=TableColumnConstraints(nullable=False, other=["<= 10"]),
            ),
            TableColumn(
                name="b",
                type="Float64",
                description="b desc",
                constraints=TableColumnConstraints(nullable=False, other=["< -1.2"]),
            ),
            TableColumn(
                name="c",
                type="String",
                description="c desc",
                constraints=TableColumnConstraints(
                    nullable=False,
                    other=[
                        "str_startswith('value_')",
                        "Two words separated by underscore.",
                    ],
                ),
            ),
        ],
    )


def test_typing_type_is_polars(schema):
    dagster_type = pandera_schema_to_dagster_type(schema)
    assert dagster_type.typing_type is pl.DataFrame


def test_name_extraction():
    schema = sample_schema_model()
    assert pandera_schema_to_dagster_type(schema).key == schema.__name__

    schema = sample_schema_model(name="foo")
    assert pandera_schema_to_dagster_type(schema).key == "foo"

    schema = sample_schema_model(title="foo", name="bar")
    assert pandera_schema_to_dagster_type(schema).key == "foo"

    schema = sample_dataframe_schema()
    assert re.match(r"DagsterPanderaDataframe\d+", pandera_schema_to_dagster_type(schema).key)

    schema = sample_dataframe_schema(title="foo", name="bar")
    assert pandera_schema_to_dagster_type(schema).key == "foo"

    schema = sample_dataframe_schema(name="foo")
    assert pandera_schema_to_dagster_type(schema).key == "foo"


# ----- VALIDATION


def test_validate_ok(dagster_type, dataframe):
    result = check_dagster_type(dagster_type, dataframe)
    assert isinstance(result, TypeCheck)
    assert result.success


def test_validate_inv_bad_value(dagster_type, dataframe):
    dataframe[0, "a"] = 11
    result = check_dagster_type(dagster_type, dataframe)
    assert not result.success


def test_validate_inv_missing_column(dagster_type, dataframe):
    dataframe = dataframe.drop(["a"])
    result = check_dagster_type(dagster_type, dataframe)
    assert not result.success


def test_validate_rejects_lazyframe(dagster_type, dataframe):
    """Pandera silently skips value-level checks on LazyFrames, so we reject."""
    result = check_dagster_type(dagster_type, dataframe.lazy())
    assert not result.success
    assert "LazyFrame" in (result.description or "")
    assert "collect()" in (result.description or "")


# ----- ASSET MATERIALIZATION (real Pandera + Dagster end-to-end)
#
# Reproduces #23714: a Polars-backed pandera schema used as an asset's
# Dagster type. Before the fix, `typing_type` resolved to `pd.DataFrame`,
# which broke materialization with Polars-aware IO managers. With the fix,
# the asset materializes successfully against the in-memory IO manager.


def test_polars_asset_materializes_with_pandera_schema():
    SchemaModel = sample_schema_model()
    PolarsPanderaType = pandera_schema_to_dagster_type(SchemaModel)

    @asset(dagster_type=PolarsPanderaType)
    def my_polars_asset() -> pl.DataFrame:
        return pl.DataFrame(DATA_OK)

    result = materialize([my_polars_asset])
    assert result.success
    output = result.output_for_node("my_polars_asset")
    assert isinstance(output, pl.DataFrame)


def test_polars_asset_materialization_fails_on_invalid_data():
    SchemaModel = sample_schema_model()
    PolarsPanderaType = pandera_schema_to_dagster_type(SchemaModel)

    bad_data = dict(DATA_OK)
    bad_data["a"] = [1, 4, 0, 10, 99]  # 99 violates le=10

    @asset(dagster_type=PolarsPanderaType)
    def bad_polars_asset() -> pl.DataFrame:
        return pl.DataFrame(bad_data)

    result = materialize([bad_polars_asset], raise_on_error=False)
    assert not result.success


def test_op_with_polars_pandera_schema_typed_output():
    SchemaModel = sample_schema_model()
    PolarsPanderaType = pandera_schema_to_dagster_type(SchemaModel)

    @op(out=Out(dagster_type=PolarsPanderaType))
    def make_df() -> pl.DataFrame:
        return pl.DataFrame(DATA_OK)

    @job
    def my_job():
        make_df()

    result = my_job.execute_in_process()
    assert result.success


def test_typing_type_reaches_io_manager():
    """Reproduces #23714: a Polars-aware IO manager reads
    ``context.dagster_type.typing_type`` to decide how to handle the value.
    Before the fix it saw ``pd.DataFrame`` even for polars schemas.
    """
    from dagster import IOManager, IOManagerDefinition

    seen: dict[str, object] = {}

    class TypingTypeAssertingIOManager(IOManager):
        def handle_output(self, context, obj):
            seen["typing_type"] = context.dagster_type.typing_type
            seen["obj_type"] = type(obj)

        def load_input(self, context):
            raise NotImplementedError

    SchemaModel = sample_schema_model()
    PolarsPanderaType = pandera_schema_to_dagster_type(SchemaModel)

    @asset(dagster_type=PolarsPanderaType, io_manager_key="custom")
    def polars_asset() -> pl.DataFrame:
        return pl.DataFrame(DATA_OK)

    result = materialize(
        [polars_asset],
        resources={
            "custom": IOManagerDefinition.hardcoded_io_manager(TypingTypeAssertingIOManager())
        },
    )
    assert result.success
    assert seen["typing_type"] is pl.DataFrame
    assert seen["obj_type"] is pl.DataFrame
