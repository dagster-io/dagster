import pytest
from dagster_pandas.constraints import (
    CategoricalColumnConstraint,
    ColumnDTypeFnConstraint,
    ColumnDTypeInSetConstraint,
    ConstraintViolationException,
    InRangeColumnConstraint,
    NonNullableColumnConstraint,
    RowCountConstraint,
    UniqueColumnConstraint,
)
from dagster_pandas.validation import PandasColumn, validate_constraints
from pandas import DataFrame, Timestamp


def test_validate_constraints_ok():
    column_constraints = [
        PandasColumn(name="foo", constraints=[ColumnDTypeInSetConstraint({"object"})]),
    ]
    dataframe = DataFrame({"foo": ["bar", "baz"]})
    assert validate_constraints(dataframe, pandas_columns=column_constraints) is None


def test_missing_column_validation():
    column_constraints = [
        PandasColumn(name="qux", constraints=[ColumnDTypeInSetConstraint({"object"})]),
    ]
    dataframe = DataFrame({"foo": ["bar", "baz"]})
    with pytest.raises(
        ConstraintViolationException, match="Required column qux not in dataframe with columns"
    ):
        validate_constraints(dataframe, pandas_columns=column_constraints)


def test_missing_column_validation_with_optional_column():
    column_constraints = [
        PandasColumn(
            name="qux", constraints=[ColumnDTypeInSetConstraint({"object"})], is_required=False
        ),
    ]
    dataframe = DataFrame({"foo": ["bar", "baz"]})
    assert validate_constraints(dataframe, pandas_columns=column_constraints) is None


@pytest.mark.parametrize(
    "column_constraints, dataframe",
    [
        (
            [PandasColumn(name="foo", constraints=[ColumnDTypeInSetConstraint({"int64"})])],
            DataFrame({"foo": ["bar", "baz"]}),
        ),
        (
            [PandasColumn(name="foo", constraints=[ColumnDTypeInSetConstraint({"object"})])],
            DataFrame({"bar": ["bar", "baz"]}),
        ),
    ],
)
def test_validate_constraints_throw_error(column_constraints, dataframe):
    with pytest.raises(ConstraintViolationException):
        validate_constraints(dataframe, pandas_columns=column_constraints)


def test_shape_validation_ok():
    assert (
        validate_constraints(
            DataFrame({"foo": [2], "bar": ["hello"]}),
            pandas_columns=[
                PandasColumn.integer_column("foo", min_value=0),
                PandasColumn.string_column("bar"),
            ],
            dataframe_constraints=[RowCountConstraint(1)],
        )
        is None
    )


def test_shape_validation_without_column_constraints():
    assert (
        validate_constraints(
            DataFrame({"foo": [2], "bar": ["hello"]}), dataframe_constraints=[RowCountConstraint(1)]
        )
        is None
    )

    with pytest.raises(ConstraintViolationException):
        validate_constraints(
            DataFrame({"foo": [2], "bar": ["hello"]}), dataframe_constraints=[RowCountConstraint(2)]
        )


def test_shape_validation_throw_error():
    with pytest.raises(ConstraintViolationException):
        validate_constraints(
            DataFrame({"foo": [2], "bar": ["hello"]}),
            pandas_columns=[
                PandasColumn.integer_column("foo", min_value=0),
                PandasColumn.string_column("bar"),
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


@pytest.mark.parametrize(
    "composer, composer_args, expected_constraints",
    [
        (PandasColumn.boolean_column, [], [ColumnDTypeFnConstraint]),
        (PandasColumn.numeric_column, [], [ColumnDTypeFnConstraint, InRangeColumnConstraint]),
        (PandasColumn.datetime_column, [], [ColumnDTypeInSetConstraint, InRangeColumnConstraint]),
        (PandasColumn.string_column, [], [ColumnDTypeFnConstraint]),
        (
            PandasColumn.categorical_column,
            [{"a", "b"}],
            [ColumnDTypeInSetConstraint, CategoricalColumnConstraint],
        ),
    ],
)
def test_datetime_column_composition(composer, composer_args, expected_constraints):
    column = composer("foo", *composer_args)
    assert isinstance(column, PandasColumn)
    assert column.name == "foo"
    assert has_constraints(column, expected_constraints)

    # Test non nullable constraint flag
    non_nullable_included_constraints = expected_constraints + [NonNullableColumnConstraint]
    non_nullable_column = composer("foo", *composer_args, non_nullable=True)
    assert has_constraints(non_nullable_column, non_nullable_included_constraints)

    # Test unique constraint flag
    distinct_included_constraints = expected_constraints + [UniqueColumnConstraint]
    distinct_column = composer("foo", *composer_args, unique=True)
    assert has_constraints(distinct_column, distinct_included_constraints)

    # Test ignore_missing_values flag
    ignore_column = composer("foo", *composer_args, ignore_missing_vals=True)
    assert has_constraints(ignore_column, expected_constraints)
    for constraint in ignore_column.constraints:
        if hasattr(constraint, "ignore_missing_vals"):
            assert constraint.ignore_missing_vals


def test_datetime_column_with_tz_validation_ok():
    assert (
        validate_constraints(
            DataFrame(
                {
                    "datetime": [Timestamp("2021-03-14T12:34:56")],
                    "datetime_utc": [Timestamp("2021-03-14T12:34:56Z")],
                    "datetime_dublin": [Timestamp("2021-03-14T12:34:56", tz="Europe/Dublin")],
                    "datetime_est": [Timestamp("2021-03-14T12:34:56", tz="US/Eastern")],
                    "datetime_chatham": [Timestamp("2021-03-14T12:34:56", tz="Pacific/Chatham")],
                    "datetime_utc_with_min_max": [Timestamp("2021-03-14T12:34:56Z")],
                }
            ),
            pandas_columns=[
                PandasColumn.datetime_column("datetime"),
                PandasColumn.datetime_column("datetime_utc", tz="UTC"),
                PandasColumn.datetime_column("datetime_dublin", tz="Europe/Dublin"),
                PandasColumn.datetime_column("datetime_est", tz="US/Eastern"),
                PandasColumn.datetime_column("datetime_chatham", tz="Pacific/Chatham"),
            ],
        )
        is None
    )


def test_datetime_column_with_min_max_constraints_ok():
    assert (
        validate_constraints(
            DataFrame(
                {
                    "datetime": [Timestamp("2021-03-14T12:34:56")],
                    "datetime_utc_min_max_no_tz": [Timestamp("2021-03-14T12:34:56Z")],
                    "datetime_utc_min_max_same_tz": [Timestamp("2021-03-14T12:34:56Z")],
                    "datetime_utc_min_max_from_different_tz": [Timestamp("2021-03-14T12:34:56Z")],
                }
            ),
            pandas_columns=[
                PandasColumn.datetime_column(
                    "datetime_utc_min_max_no_tz",
                    tz="UTC",
                    min_datetime=Timestamp.min,
                    max_datetime=Timestamp.max,
                ),
                PandasColumn.datetime_column(
                    "datetime_utc_min_max_same_tz",
                    tz="UTC",
                    min_datetime=Timestamp("2021-01-01T00:00:00Z"),
                    max_datetime=Timestamp("2021-12-01T00:00:00Z"),
                ),
                PandasColumn.datetime_column(
                    "datetime_utc_min_max_from_different_tz",
                    tz="UTC",
                    min_datetime=Timestamp("2021-01-01T00:00:00Z", tz="US/Eastern"),
                    max_datetime=Timestamp("2021-12-01T00:00:00Z"),
                ),
            ],
        )
        is None
    )


def test_datetime_column_with_tz_validation_fails_when_incorrect_tz():
    with pytest.raises(ConstraintViolationException):
        validate_constraints(
            DataFrame({"datetime_utc": [Timestamp("2021-03-14T12:34:56")],}),
            pandas_columns=[PandasColumn.datetime_column("datetime_utc", tz="UTC"),],
        )
