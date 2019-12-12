import pytest
from dagster_pandas.constraints import ColumnTypeConstraint, ConstraintViolationException
from dagster_pandas.validation import PandasColumn, validate_collection_schema
from pandas import DataFrame


def test_validate_collection_schema_ok():
    collection_schema = [
        PandasColumn(name='foo', constraints=[ColumnTypeConstraint('object')]),
    ]
    dataframe = DataFrame({'foo': ['bar', 'baz']})
    assert validate_collection_schema(collection_schema, dataframe) is None


@pytest.mark.parametrize(
    'collection_schema, dataframe',
    [
        (
            [PandasColumn(name='foo', constraints=[ColumnTypeConstraint('int64')])],
            DataFrame({'foo': ['bar', 'baz']}),
        ),
        (
            [PandasColumn(name='foo', constraints=[ColumnTypeConstraint('object')])],
            DataFrame({'bar': ['bar', 'baz']}),
        ),
    ],
)
def test_validate_collection_schema_throw_error(collection_schema, dataframe):
    with pytest.raises(ConstraintViolationException):
        validate_collection_schema(collection_schema, dataframe)
