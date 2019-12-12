import pytest
from dagster_pandas.constraints import (
    CategoricalColumnConstraint,
    ColumnExistsConstraint,
    ColumnTypeConstraint,
    ConstraintViolationException,
    NonNullableColumnConstraint,
)
from pandas import DataFrame


def test_column_exists_constraint():
    test_dataframe = DataFrame({'foo': ['baz']})
    assert ColumnExistsConstraint().validate(test_dataframe, 'foo') is None

    with pytest.raises(ConstraintViolationException):
        ColumnExistsConstraint().validate(test_dataframe, 'bar')


def test_column_type_constraint():
    test_dataframe = DataFrame({'foo': ['baz']})
    assert ColumnTypeConstraint('object').validate(test_dataframe, 'foo') is None

    with pytest.raises(ConstraintViolationException):
        ColumnTypeConstraint('int64').validate(test_dataframe, 'foo')


def test_non_nullable_column_constraint():
    test_dataframe = DataFrame({'foo': ['baz']})
    assert NonNullableColumnConstraint().validate(test_dataframe, 'foo') is None

    bad_test_dataframe = DataFrame({'foo': ['baz', None]})
    with pytest.raises(ConstraintViolationException):
        NonNullableColumnConstraint().validate(bad_test_dataframe, 'foo')


def test_categorical_column_constraint():
    test_dataframe = DataFrame({'foo': ['bar', 'baz', 'bar', 'bar']})
    assert CategoricalColumnConstraint({'bar', 'baz'}).validate(test_dataframe, 'foo') is None

    bad_test_dataframe = DataFrame({'foo': ['bar', 'qux', 'bar', 'bar']})
    with pytest.raises(ConstraintViolationException):
        CategoricalColumnConstraint({'bar', 'baz'}).validate(bad_test_dataframe, 'foo')
