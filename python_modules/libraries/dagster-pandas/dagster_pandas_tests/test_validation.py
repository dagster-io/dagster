import pytest
from dagster_pandas.constraints import (
    CategoricalColumnConstraint,
    ColumnExistsConstraint,
    ColumnTypeConstraint,
    ConstraintViolationException,
    InRangeColumnConstraint,
    NonNullableColumnConstraint,
    RowCountConstraint,
    UniqueColumnConstraint,
)
from dagster_pandas.validation import PandasColumn, validate_constraints
from pandas import DataFrame


def test_validate_constraints_ok():
    column_constraints = [
        PandasColumn(name='foo', constraints=[ColumnTypeConstraint('object')]),
    ]
    dataframe = DataFrame({'foo': ['bar', 'baz']})
    assert validate_constraints(dataframe, pandas_columns=column_constraints) is None


@pytest.mark.parametrize(
    'column_constraints, dataframe',
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
def test_validate_constraints_throw_error(column_constraints, dataframe):
    with pytest.raises(ConstraintViolationException):
        validate_constraints(dataframe, pandas_columns=column_constraints)


def test_shape_validation_ok():
    assert (
        validate_constraints(
            DataFrame({'foo': [2], 'bar': ['hello']}),
            pandas_columns=[
                PandasColumn.integer_column('foo', min_value=0),
                PandasColumn.string_column('bar'),
            ],
            dataframe_constraints=[RowCountConstraint(1)],
        )
        is None
    )


def test_shape_validation_without_column_constraints():
    assert (
        validate_constraints(
            DataFrame({'foo': [2], 'bar': ['hello']}), dataframe_constraints=[RowCountConstraint(1)]
        )
        is None
    )

    with pytest.raises(ConstraintViolationException):
        validate_constraints(
            DataFrame({'foo': [2], 'bar': ['hello']}), dataframe_constraints=[RowCountConstraint(2)]
        )


def test_shape_validation_throw_error():
    with pytest.raises(ConstraintViolationException):
        validate_constraints(
            DataFrame({'foo': [2], 'bar': ['hello']}),
            pandas_columns=[
                PandasColumn.integer_column('foo', min_value=0),
                PandasColumn.string_column('bar'),
            ],
            dataframe_constraints=[RowCountConstraint(2)],
        )


def has_constraints(column, constraints):
    for constraint in constraints:
        if not any(
            [isinstance(col_constraint, constraint) for col_constraint in column.constraints]
        ):
            return False
    return True


def test_exists_column_composition():
    exists_column = PandasColumn.exists('foo')
    assert isinstance(exists_column, PandasColumn)
    assert len(exists_column.constraints) == 1
    assert isinstance(exists_column.constraints[0], ColumnExistsConstraint)


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
