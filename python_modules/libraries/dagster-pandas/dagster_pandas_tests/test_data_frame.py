from dagster_pandas.constraints import ColumnTypeConstraint
from dagster_pandas.data_frame import (
    create_dagster_pandas_dataframe_type,
    create_named_dataframe,
    create_typed_dataframe,
)
from dagster_pandas.validation import PandasColumn


def test_create_pandas_dataframe_dagster_type():
    TestDataFrame = create_dagster_pandas_dataframe_type(
        name='TestDataFrame',
        type_check=lambda value: True,
        columns=[PandasColumn(name='foo', constraints=[ColumnTypeConstraint('int64')])],
    )
    assert isinstance(TestDataFrame, type)


def test_create_typed_dataframe():
    dataframe_type = create_typed_dataframe('TestDataFrame', {'foo': 'int64', 'bar': 'object'})
    assert dataframe_type
    assert isinstance(dataframe_type, type)


def test_create_named_dataframe():
    dataframe_type = create_named_dataframe('TestDataFrame', ['foo', 'bar'])
    assert dataframe_type
    assert isinstance(dataframe_type, type)
