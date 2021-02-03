from dagster_pandas.constraints import (
    ColumnAggregateConstraintWithMetadata,
    ColumnConstraintWithMetadata,
    ColumnRangeConstraintWithMetadata,
    ColumnWithMetadataException,
    ConstraintWithMetadata,
    ConstraintWithMetadataException,
    DataFrameWithMetadataException,
    MultiAggregateConstraintWithMetadata,
    MultiColumnConstraintWithMetadata,
    MultiConstraintWithMetadata,
    StrictColumnsWithMetadata,
)
from pandas import DataFrame


def basic_validation_function(inframe):
    if isinstance(inframe, DataFrame):
        return (True, {})
    else:
        return (
            False,
            {"expectation": "a " + DataFrame.__name__, "actual": "a " + type(inframe).__name__},
        )


basic_confirmation_function = ConstraintWithMetadata(
    description="this constraint confirms that table is correct type",
    validation_fn=basic_validation_function,
    resulting_exception=DataFrameWithMetadataException,
    raise_or_typecheck=False,
)


basic_multi_constraint = MultiConstraintWithMetadata(
    description="this constraint confirms that table is correct type",
    validation_fn_arr=[basic_validation_function],
    resulting_exception=DataFrameWithMetadataException,
    raise_or_typecheck=False,
)


def test_failed_basic():
    assert not basic_confirmation_function.validate([]).success


def test_basic():
    assert basic_confirmation_function.validate(DataFrame())


def test_failed_multi():
    mul_val = basic_multi_constraint.validate([]).metadata_entries[0].entry_data.data
    assert mul_val["expected"] == {"basic_validation_function": "a DataFrame"}
    assert mul_val["actual"] == {"basic_validation_function": "a list"}


def test_success_multi():
    mul_val = basic_multi_constraint.validate(DataFrame())
    assert mul_val.success == True
    assert mul_val.metadata_entries == []


def test_failed_strict():
    strict_column = StrictColumnsWithMetadata(["base_test"], raise_or_typecheck=False)
    assert not strict_column.validate(DataFrame()).success


def test_successful_strict():
    strict_column = StrictColumnsWithMetadata([], raise_or_typecheck=False)
    assert strict_column.validate(DataFrame()).success


def test_column_constraint():
    def column_num_validation_function(value):
        return (isinstance(value, int), {})

    df = DataFrame({"foo": [1, 2], "bar": ["a", 2], "baz": [1, "a"]})
    column_val = ColumnConstraintWithMetadata(
        "Confirms type of column values",
        column_num_validation_function,
        ColumnWithMetadataException,
        raise_or_typecheck=False,
    )
    val = column_val.validate(df, *df.columns).metadata_entries[0].entry_data.data
    assert {"bar": ["row 0"], "baz": ["row 1"]} == val["offending"]
    assert {"bar": ["a"], "baz": ["a"]} == val["actual"]


def test_multi_val_constraint():
    def column_num_validation_function(value):
        return (value >= 3, {})

    df = DataFrame({"foo": [1, 2], "bar": [3, 2], "baz": [1, 4]})
    column_val = ColumnConstraintWithMetadata(
        "Confirms values greater than 3",
        column_num_validation_function,
        ColumnWithMetadataException,
        raise_or_typecheck=False,
    )
    val = column_val.validate(df, *df.columns).metadata_entries[0].entry_data.data
    assert {"foo": ["row 0", "row 1"], "bar": ["row 1"], "baz": ["row 0"]} == val["offending"]
    assert {"foo": [1, 2], "bar": [2], "baz": [1]} == val["actual"]


def test_multi_column_constraint():
    def col_val_three(value):
        """
        returns values greater than or equal to 3
        """
        return (value >= 2, {})

    def col_val_two(value):
        """
        returns values less than 2
        """
        return (value < 2, {})

    df = DataFrame({"foo": [1, 2, 3], "bar": [3, 2, 1], "baz": [1, 4, 5]})
    column_val = MultiColumnConstraintWithMetadata(
        "Complex number confirmation",
        dict([("bar", [col_val_two, col_val_three]), ("baz", [col_val_three])]),
        ColumnWithMetadataException,
        raise_or_typecheck=False,
    )
    val = column_val.validate(df).metadata_entries[0].entry_data.data
    assert {
        "bar": {
            "col_val_two": "values less than 2",
            "col_val_three": "values greater than or equal to 3",
        },
        "baz": {"col_val_three": "values greater than or equal to 3"},
    } == val["expected"]
    assert {
        "bar": {"col_val_two": ["row 0", "row 1"], "col_val_three": ["row 2"]},
        "baz": {"col_val_three": ["row 0"]},
    } == val["offending"]
    assert {
        "bar": {"col_val_two": [3, 2], "col_val_three": [1]},
        "baz": {"col_val_three": [1]},
    } == val["actual"]


def test_aggregate_constraint():
    def column_mean_validation_function(data):
        return (data.mean() == 1, {})

    df = DataFrame(
        {
            "foo": [1, 2],
            "bar": [1, 1],
        }
    )
    aggregate_val = ColumnAggregateConstraintWithMetadata(
        "Confirms column means equal to 1",
        column_mean_validation_function,
        ConstraintWithMetadataException,
        raise_or_typecheck=False,
    )
    val = aggregate_val.validate(df, *df.columns).metadata_entries[0].entry_data.data
    assert {"foo"} == val["offending"]
    assert [1, 2] == val["actual"]["foo"]


def test_multi_agg_constraint():
    def column_val_1(data):
        """checks column mean equal to 1"""
        return (data.mean() == 1, {})

    def column_val_2(data):
        """checks column mean equal to 1.5"""
        return (data.mean() == 1.5, {})

    df = DataFrame(
        {
            "foo": [1, 2],
            "bar": [1, 1],
        }
    )
    aggregate_val = MultiAggregateConstraintWithMetadata(
        "Confirms column means equal to 1",
        dict([("bar", [column_val_1, column_val_2]), ("foo", [column_val_1, column_val_2])]),
        ConstraintWithMetadataException,
        raise_or_typecheck=False,
    )
    val = aggregate_val.validate(df).metadata_entries[0].entry_data.data
    assert val["expected"] == {
        "bar": {"column_val_2": "checks column mean equal to 1.5"},
        "foo": {"column_val_1": "checks column mean equal to 1"},
    }
    assert val["offending"] == {
        "bar": {"column_val_2": "a violation"},
        "foo": {"column_val_1": "a violation"},
    }


def test_range_constraint():
    df = DataFrame({"foo": [1, 2], "bar": [3, 2], "baz": [1, 4]})
    range_val = ColumnRangeConstraintWithMetadata(1, 2.5, raise_or_typecheck=False)
    val = range_val.validate(df).metadata_entries[0].entry_data.data
    assert {"bar": ["row 0"], "baz": ["row 1"]} == val["offending"]
    assert {"bar": [3], "baz": [4]} == val["actual"]
    range_val = ColumnRangeConstraintWithMetadata(raise_or_typecheck=False)
    assert range_val.validate(df).success
