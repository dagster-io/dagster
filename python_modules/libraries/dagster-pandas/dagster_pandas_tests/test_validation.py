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
from pandas import DataFrame


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
