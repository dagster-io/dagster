import pytest
from dagster_pandas.constraints import (
    CategoricalColumnConstraint,
    ColumnDTypeInSetConstraint,
    ConstraintViolationException,
    InRangeColumnConstraint,
    MaxValueColumnConstraint,
    MinValueColumnConstraint,
    NonNullableColumnConstraint,
    RowCountConstraint,
    StrictColumnsConstraint,
    UniqueColumnConstraint,
)
from numpy import NaN
from pandas import DataFrame

NAN_VALUES = [
    NaN,
    None,
]


def test_column_unique_constraint():
    test_dataframe = DataFrame({"foo": ["foo", "bar", "baz"]})
    assert UniqueColumnConstraint(ignore_missing_vals=False).validate(test_dataframe, "foo") is None

    bad_test_dataframe = DataFrame({"foo": ["foo", "foo", "baz"]})
    with pytest.raises(ConstraintViolationException):
        UniqueColumnConstraint(ignore_missing_vals=False).validate(bad_test_dataframe, "foo")


def test_column_unique_constraint_ignore_nan():
    for nullable_value in NAN_VALUES:
        test_dataframe = DataFrame({"foo": [nullable_value, "bar", "baz"]})
        assert (
            UniqueColumnConstraint(ignore_missing_vals=True).validate(test_dataframe, "foo") is None
        )

        test_dataframe = DataFrame({"foo": [nullable_value, nullable_value, "baz"]})
        assert (
            UniqueColumnConstraint(ignore_missing_vals=True).validate(test_dataframe, "foo") is None
        )

        test_dataframe = DataFrame({"foo": ["bar", "bar", nullable_value]})
        with pytest.raises(ConstraintViolationException):
            UniqueColumnConstraint(ignore_missing_vals=False).validate(test_dataframe, "foo")

        test_dataframe = DataFrame({"foo": [nullable_value, nullable_value, "baz"]})
        with pytest.raises(ConstraintViolationException):
            UniqueColumnConstraint(ignore_missing_vals=False).validate(test_dataframe, "foo")


def test_column_type_constraint():
    test_dataframe = DataFrame({"foo": ["baz"]})
    assert ColumnDTypeInSetConstraint({"object"}).validate(test_dataframe, "foo") is None

    with pytest.raises(ConstraintViolationException):
        ColumnDTypeInSetConstraint({"int64"}).validate(test_dataframe, "foo")


def test_non_nullable_column_constraint():
    test_dataframe = DataFrame({"foo": ["baz"]})
    assert NonNullableColumnConstraint().validate(test_dataframe, "foo") is None

    bad_test_dataframe = DataFrame({"foo": ["baz", None]})
    with pytest.raises(ConstraintViolationException):
        NonNullableColumnConstraint().validate(bad_test_dataframe, "foo")


def test_categorical_column_constraint():
    test_dataframe = DataFrame({"foo": ["bar", "baz", "bar", "bar"]})
    assert (
        CategoricalColumnConstraint({"bar", "baz"}, ignore_missing_vals=False).validate(
            test_dataframe, "foo"
        )
        is None
    )

    bad_test_dataframe = DataFrame({"foo": ["bar", "qux", "bar", "bar"]})
    with pytest.raises(ConstraintViolationException):
        CategoricalColumnConstraint({"bar", "baz"}, ignore_missing_vals=False).validate(
            bad_test_dataframe, "foo"
        )


def test_categorical_column_constraint_ignore_nan():
    for nullable in NAN_VALUES:
        test_dataframe = DataFrame({"foo": ["red", "blue", "green", nullable]})
        assert (
            CategoricalColumnConstraint(
                {"red", "blue", "green"}, ignore_missing_vals=True
            ).validate(test_dataframe, "foo")
            is None
        )

        test_dataframe = DataFrame({"foo": ["red", "yellow", "green", nullable, nullable]})
        with pytest.raises(ConstraintViolationException):
            CategoricalColumnConstraint(
                {"red", "blue", "green"}, ignore_missing_vals=True
            ).validate(test_dataframe, "foo")


def test_min_value_column_constraint():
    test_dataframe = DataFrame({"foo": [1, 1, 2, 3]})
    assert (
        MinValueColumnConstraint(0, ignore_missing_vals=False).validate(test_dataframe, "foo")
        is None
    )
    with pytest.raises(ConstraintViolationException):
        MinValueColumnConstraint(2, ignore_missing_vals=False).validate(test_dataframe, "foo")


def test_min_valid_column_constraint_ignore_nan():
    for nullable in NAN_VALUES:
        test_dataframe = DataFrame({"foo": [1, 1, 2, 3, nullable]})
        assert (
            MinValueColumnConstraint(0, ignore_missing_vals=True).validate(test_dataframe, "foo")
            is None
        )

        with pytest.raises(ConstraintViolationException):
            MinValueColumnConstraint(3, ignore_missing_vals=True).validate(test_dataframe, "foo")


def test_max_value_column_constraint():
    test_dataframe = DataFrame({"foo": [1, 1, 2, 3]})
    assert (
        MaxValueColumnConstraint(5, ignore_missing_vals=False).validate(test_dataframe, "foo")
        is None
    )
    with pytest.raises(ConstraintViolationException):
        MaxValueColumnConstraint(2, ignore_missing_vals=False).validate(test_dataframe, "foo")


def test_max_valid_column_constraint_ignore_nan():
    for nullable in NAN_VALUES:
        test_dataframe = DataFrame({"foo": [1, 1, 2, 3, nullable]})
        assert (
            MaxValueColumnConstraint(5, ignore_missing_vals=True).validate(test_dataframe, "foo")
            is None
        )

        with pytest.raises(ConstraintViolationException):
            MaxValueColumnConstraint(2, ignore_missing_vals=True).validate(test_dataframe, "foo")


def test_in_range_value_column_constraint():
    test_dataframe = DataFrame({"foo": [1, 1, 2, 3]})
    assert (
        InRangeColumnConstraint(1, 4, ignore_missing_vals=False).validate(test_dataframe, "foo")
        is None
    )
    with pytest.raises(ConstraintViolationException):
        InRangeColumnConstraint(2, 3, ignore_missing_vals=False).validate(test_dataframe, "foo")


def test_in_range_value_column_constraint_ignore_nan():
    for nullable in NAN_VALUES:
        test_dataframe = DataFrame({"foo": [1, 1, 2, 3, nullable]})
        assert (
            InRangeColumnConstraint(1, 4, ignore_missing_vals=True).validate(test_dataframe, "foo")
            is None
        )

        with pytest.raises(ConstraintViolationException):
            InRangeColumnConstraint(2, 3, ignore_missing_vals=True).validate(test_dataframe, "foo")


def test_strict_columns_constraint():
    assert (
        StrictColumnsConstraint(["foo", "bar"]).validate(DataFrame({"foo": [1, 2], "bar": [1, 2]}))
        is None
    )
    with pytest.raises(ConstraintViolationException):
        StrictColumnsConstraint(["foo", "bar"]).validate(
            DataFrame({"foo": [1, 2], "bar": [1, 2], "baz": [1, 2]})
        )

    assert (
        StrictColumnsConstraint(["foo", "bar"], enforce_ordering=True).validate(
            DataFrame([[1, 2], [1, 2]], columns=["foo", "bar"])
        )
        is None
    )
    with pytest.raises(ConstraintViolationException):
        StrictColumnsConstraint(["foo", "bar"], enforce_ordering=True).validate(
            DataFrame([[1, 2], [1, 2]], columns=["bar", "foo"])
        )


def test_row_count_constraint():
    test_dataframe = DataFrame({"foo": [1, 2, 3, 4, 5, 6]})
    assert RowCountConstraint(6).validate(test_dataframe) is None
    with pytest.raises(ConstraintViolationException):
        RowCountConstraint(5).validate(test_dataframe)

    assert (
        RowCountConstraint(5, error_tolerance=1).validate(DataFrame({"foo": [1, 2, 3, 4]})) is None
    )
    with pytest.raises(ConstraintViolationException):
        assert RowCountConstraint(5, error_tolerance=1).validate(DataFrame({"foo": [1, 2]}))

    assert (
        RowCountConstraint(5, error_tolerance=1).validate(DataFrame({"foo": [1, 2, 3, 4, 5, 6]}))
        is None
    )
    with pytest.raises(ConstraintViolationException):
        assert RowCountConstraint(5, error_tolerance=1).validate(
            DataFrame({"foo": [1, 2, 3, 4, 5, 6, 7]})
        )
