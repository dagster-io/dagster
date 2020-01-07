import pytest
from dagster_pandas.constraints import (
    CategoricalColumnConstraint,
    ColumnTypeConstraint,
    ConstraintViolationException,
    InRangeColumnConstraint,
    NonNullableColumnConstraint,
    RowCountConstraint,
    UniqueColumnConstraint,
)
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


def test_shape_validation_ok():
    assert (
        validate_collection_schema(
            [PandasColumn.integer_column('foo', min_value=0), PandasColumn.string_column('bar')],
            DataFrame({'foo': [2], 'bar': ['hello']}),
            dataframe_constraints=[RowCountConstraint(1)],
        )
        is None
    )


def test_shape_validation_throw_error():
    with pytest.raises(ConstraintViolationException):
        validate_collection_schema(
            [PandasColumn.integer_column('foo', min_value=0), PandasColumn.string_column('bar')],
            DataFrame({'foo': [2], 'bar': ['hello']}),
            dataframe_constraints=[RowCountConstraint(2)],
        )


def has_constraints(column, constraints):
    for constraint in constraints:
        if not any(
            [isinstance(col_constraint, constraint) for col_constraint in column.constraints]
        ):
            return False
    return True


@pytest.mark.parametrize(
    'composer, composer_args, expected_constraints',
    [
        (PandasColumn.boolean_column, [], [ColumnTypeConstraint]),
        (
            PandasColumn.numeric_column,
            [{'int64', 'float64'}],
            [ColumnTypeConstraint, InRangeColumnConstraint],
        ),
        (PandasColumn.datetime_column, [], [ColumnTypeConstraint, InRangeColumnConstraint]),
        (PandasColumn.string_column, [], [ColumnTypeConstraint]),
        (
            PandasColumn.categorical_column,
            [{'a', 'b'}],
            [ColumnTypeConstraint, CategoricalColumnConstraint],
        ),
    ],
)
def test_datetime_column_composition(composer, composer_args, expected_constraints):
    column = composer('foo', *composer_args)
    assert isinstance(column, PandasColumn)
    assert column.name == 'foo'
    assert has_constraints(column, expected_constraints)

    # Test non nullable constraint flag
    exists_included_constraints = expected_constraints + [NonNullableColumnConstraint]
    non_nullable_column = composer('foo', *composer_args, exists=True)
    assert has_constraints(non_nullable_column, exists_included_constraints)

    # Test unique constraint flag
    distinct_included_constraints = expected_constraints + [UniqueColumnConstraint]
    distinct_column = composer('foo', *composer_args, unique=True)
    assert has_constraints(distinct_column, distinct_included_constraints)
