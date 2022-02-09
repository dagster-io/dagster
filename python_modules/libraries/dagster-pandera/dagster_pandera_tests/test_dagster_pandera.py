# pylint: disable=redefined-outer-name

import pytest

import pandera as pa
import pandas as pd
from dagster.core.definitions.event_metadata import TableSchemaMetadataEntryData
from dagster.core.definitions.event_metadata.table import TableColumnConstraints, TableSchema, TableColumn

from dagster_pandera import pandera_schema_to_dagster_type
from dagster import check_dagster_type, DagsterType, TypeCheck

# from modin.pandas import DataFrame as ModinDataFrame
# from databricks.koalas import DataFrame as KoalasDataFrame

# ########################
# ##### FIXTURES
# ########################

# @pytest.fixture(params=[pd.DataFrame, ModinDataFrame, KoalasDataFrame], ids=["pandas", "modin", "koalas"])
# def dataframe(request):
#     df_cls = request.param
@pytest.fixture
def dataframe():
    df_cls = pd.DataFrame
    return df_cls(
        {
            "a": [1, 4, 0, 10, 9],
            "b": [-1.3, -1.4, -2.9, -10.1, -20.4],
            "c": ["value_1", "value_2", "value_3", "value_2", "value_1"],
        }
    )


class SampleSchemaModel(pa.SchemaModel):

    a: pa.typing.Series[int] = pa.Field(le=10, description="a desc")
    b: pa.typing.Series[float] = pa.Field(lt=-1.2, description="b desc")
    c: pa.typing.Series[str] = pa.Field(str_startswith="value_", description="c desc")

    @pa.check("c")
    def c_check(cls, series: pa.typing.Series[str]) -> pa.typing.Series[bool]:
        """Two words separated by underscore"""
        return series.str.split("_", expand=True).shape[1] == 2

SampleDataframeSchema = pa.DataFrameSchema(
    {
        "a": pa.Column(int, checks=pa.Check.le(10), description='a desc'),
        "b": pa.Column(float, checks=pa.Check.lt(-1.2), description='b desc'),
        "c": pa.Column(
            str,
            description='c desc',
            checks=[
                pa.Check.str_startswith("value_"),
                # define custom checks as functions that take a series as input and
                # outputs a boolean or boolean Series
                pa.Check(lambda s: s.str.split("_", expand=True).shape[1] == 2, description="Two words separated by underscore"),
            ],
        ),
    }
)

# @pytest.fixture(params=[SampleDataframeSchema, SampleSchemaModel], ids=["regular_schema", "schema_model"])
# def schema(request):
#     return request.param

@pytest.fixture
def schema(request):
    # return SampleDataframeSchema
    return SampleSchemaModel



@pytest.fixture
def dagster_type(schema):
    return pandera_schema_to_dagster_type(schema)


def test_pandera_schema_to_dagster_type(schema):
    dagster_type = pandera_schema_to_dagster_type(schema)
    assert isinstance(dagster_type, DagsterType)
    assert len(dagster_type.metadata_entries) == 1
    schema_entry = dagster_type.metadata_entries[0]
    assert isinstance(schema_entry.entry_data, TableSchemaMetadataEntryData)
    assert schema_entry.entry_data.schema == TableSchema(
        columns=[
            TableColumn(
                name="a",
                type="int64",
                description="a desc",
                constraints=TableColumnConstraints(nullable=False, other=["less_than_or_equal_to(10)"]),
            ),
            TableColumn(
                name="b",
                type="float64",
                description="b desc",
                constraints=TableColumnConstraints(nullable=False, other=["less_than(-1.2)"]),
            ),
            # TableColumn(
            #     name="c",
            #     type="str",
            #     description="c desc",
            #     constraints=TableColumnConstraints(
            #         nullable=False,
            #         other=[
            #             "str_startswith(value_)",
            #             "two words separated by underscore",
            #         ],
            #     ),
            # ),
        ]
    )


# def test_validate_valid_dataframe(dagster_type, dataframe):
#     result = check_dagster_type(dagster_type, dataframe)
#     assert isinstance(result, TypeCheck)
#     assert result.success

# def test_pandera_schema_to_table_schema(schema):
#     tschema = pandera_schema_to_table_schema(schema)
#     assert isinstance(tschema, TableSchema)
#
#     assert tschema == TableSchema(
#         columns=[
#             TableColumn(
#                 name="a",
#                 # constraints=TableColumnConstraints(
#                 #
#                 # )
#             ),
