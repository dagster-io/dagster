import pytest
from dagster_pandas.constraints import (
    CategoricalColumnConstraint,
    ColumnExistsConstraint,
    ColumnTypeConstraint,
    ConstraintViolationException,
    InRangeColumnConstraint,
    MaxValueColumnConstraint,
    MinValueColumnConstraint,
    NonNullableColumnConstraint,
    UniqueColumnConstraint,
)
from pandas import DataFrame


def test_column_exists_constraint():
    test_dataframe = DataFrame({'foo': ['baz']})
    assert ColumnExistsConstraint().validate(test_dataframe, 'foo') is None

    with pytest.raises(ConstraintViolationException):
        ColumnExistsConstraint().validate(test_dataframe, 'bar')


def test_column_unique_constraint():
    test_dataframe = DataFrame({'foo': ['foo', 'bar', 'baz']})
    assert UniqueColumnConstraint().validate(test_dataframe, 'foo') is None

    bad_test_dataframe = DataFrame({'foo': ['foo', 'foo', 'baz']})
    with pytest.raises(ConstraintViolationException):
        UniqueColumnConstraint().validate(bad_test_dataframe, 'foo')


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


def test_min_value_column_constraint():
    test_dataframe = DataFrame({'foo': [1, 1, 2, 3]})
    assert MinValueColumnConstraint(0).validate(test_dataframe, 'foo') is None
    with pytest.raises(ConstraintViolationException):
        assert MinValueColumnConstraint(2).validate(test_dataframe, 'foo')


def test_max_value_column_constraint():
    test_dataframe = DataFrame({'foo': [1, 1, 2, 3]})
    assert MaxValueColumnConstraint(5).validate(test_dataframe, 'foo') is None
    with pytest.raises(ConstraintViolationException):
        assert MinValueColumnConstraint(2).validate(test_dataframe, 'foo')


def test_in_range_value_column_constraint():
    test_dataframe = DataFrame({'foo': [1, 1, 2, 3]})
    assert InRangeColumnConstraint(1, 4).validate(test_dataframe, 'foo') is None
    with pytest.raises(ConstraintViolationException):
        assert InRangeColumnConstraint(2, 3).validate(test_dataframe, 'foo')
