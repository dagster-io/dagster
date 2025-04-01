from dagster import DagsterType, Out, Output, graph, op
from dagster_pandas.constraints import (
    ColumnWithMetadataException,
    ConstraintWithMetadataException,
    MultiAggregateConstraintWithMetadata,
    MultiColumnConstraintWithMetadata,
    StrictColumnsWithMetadata,
    all_unique_validator,
    column_range_validation_factory,
    dtype_in_set_validation_factory,
    nonnull,
)
from dagster_pandas.data_frame import create_structured_dataframe_type
from numpy import float64, int64
from pandas import DataFrame

dtype_is_num_validator = nonnull(dtype_in_set_validation_factory((int, float, int64, float64)))

in_range_validator = column_range_validation_factory(1, 3, ignore_missing_vals=True)

column_validator = MultiColumnConstraintWithMetadata(
    "confirms values are numbers in a range",
    {"foo": [dtype_is_num_validator, in_range_validator], "bar": [dtype_is_num_validator]},
    ColumnWithMetadataException,
    raise_or_typecheck=False,
)

aggregate_validator = MultiAggregateConstraintWithMetadata(
    "confirms all values are unique",
    {"bar": [all_unique_validator]},
    ConstraintWithMetadataException,
    raise_or_typecheck=False,
)


dataframe_validator = StrictColumnsWithMetadata(["foo", "bar"], raise_or_typecheck=False)


def test_structured_type_creation():
    ntype = create_structured_dataframe_type(
        "NumericType",
        columns_validator=column_validator,
        columns_aggregate_validator=aggregate_validator,
        dataframe_validator=dataframe_validator,
    )
    assert isinstance(ntype, DagsterType)


def test_successful_type_eval():
    ntype = create_structured_dataframe_type(
        "NumericType",
        columns_validator=column_validator,
        columns_aggregate_validator=aggregate_validator,
        dataframe_validator=dataframe_validator,
    )

    @op(out={"basic_dataframe": Out(dagster_type=ntype)})
    def create_dataframe(_):
        yield Output(
            DataFrame({"foo": [1, 2, 3], "bar": [9, 10, 11]}),
            output_name="basic_dataframe",
        )

    @graph
    def basic_graph():
        return create_dataframe()

    result = basic_graph.execute_in_process()
    assert result.success


def test_failing_type_eval_column():
    ntype = create_structured_dataframe_type(
        "NumericType",
        columns_validator=column_validator,
        columns_aggregate_validator=aggregate_validator,
        dataframe_validator=dataframe_validator,
    )

    @op(out={"basic_dataframe": Out(dagster_type=ntype)})
    def create_dataframe(_):
        yield Output(
            DataFrame({"foo": [1, "a", 7], "bar": [9, 10, 11]}),
            output_name="basic_dataframe",
        )

    @graph
    def basic_graph():
        return create_dataframe()

    result = basic_graph.execute_in_process(raise_on_error=False)
    output = next(item for item in result.all_node_events if item.is_successful_output)
    output_data = output.event_specific_data.type_check_data  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    output_metadata = output_data.metadata  # pyright: ignore[reportOptionalMemberAccess]
    assert len(output_metadata) == 1
    column_const_data = output_metadata["columns-constraint-metadata"].data  # pyright: ignore[reportAttributeAccessIssue]
    assert column_const_data["expected"] == {
        "foo": {
            "in_range_validation_fn": in_range_validator.__doc__.strip(),  # pyright: ignore[reportOptionalMemberAccess]
            "dtype_in_set_validation_fn": dtype_is_num_validator.__doc__.strip(),  # pyright: ignore[reportOptionalMemberAccess]
        }
    }
    assert column_const_data["offending"] == {
        "foo": {
            "dtype_in_set_validation_fn": ["row 1"],
            "in_range_validation_fn": ["row 1", "row 2"],
        }
    }
    assert column_const_data["actual"] == {
        "foo": {"dtype_in_set_validation_fn": ["a"], "in_range_validation_fn": ["a", 7]}
    }


def test_failing_type_eval_aggregate():
    ntype = create_structured_dataframe_type(
        "NumericType",
        columns_validator=column_validator,
        columns_aggregate_validator=aggregate_validator,
        dataframe_validator=dataframe_validator,
    )

    @op(out={"basic_dataframe": Out(dagster_type=ntype)})
    def create_dataframe(_):
        yield Output(
            DataFrame({"foo": [1, 2, 3], "bar": [9, 10, 10]}),
            output_name="basic_dataframe",
        )

    @graph
    def basic_graph():
        return create_dataframe()

    result = basic_graph.execute_in_process(raise_on_error=False)
    output = next(item for item in result.all_node_events if item.is_successful_output)
    output_data = output.event_specific_data.type_check_data  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    output_metadata = output_data.metadata  # pyright: ignore[reportOptionalMemberAccess]
    assert len(output_metadata) == 1
    column_const = output_metadata["column-aggregates-constraint-metadata"]
    column_const_data = column_const.data  # pyright: ignore[reportAttributeAccessIssue]
    assert column_const_data["expected"] == {
        "bar": {"all_unique_validator": all_unique_validator.__doc__.strip()}  # pyright: ignore[reportOptionalMemberAccess]
    }
    assert column_const_data["offending"] == {"bar": {"all_unique_validator": "a violation"}}
    assert column_const_data["actual"] == {"bar": {"all_unique_validator": [10.0]}}


def test_failing_type_eval_dataframe():
    ntype = create_structured_dataframe_type(
        "NumericType",
        columns_validator=column_validator,
        columns_aggregate_validator=aggregate_validator,
        dataframe_validator=dataframe_validator,
    )

    @op(out={"basic_dataframe": Out(dagster_type=ntype)})
    def create_dataframe(_):
        yield Output(
            DataFrame({"foo": [1, 2, 3], "baz": [9, 10, 10]}),
            output_name="basic_dataframe",
        )

    @graph
    def basic_graph():
        return create_dataframe()

    result = basic_graph.execute_in_process(raise_on_error=False)
    output = next(item for item in result.all_node_events if item.is_successful_output)
    output_data = output.event_specific_data.type_check_data  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    output_metadata = output_data.metadata  # pyright: ignore[reportOptionalMemberAccess]
    assert len(output_metadata) == 1
    column_const_data = output_metadata["dataframe-constraint-metadata"].data  # pyright: ignore[reportAttributeAccessIssue]
    assert column_const_data["expected"] == ["foo", "bar"]
    assert column_const_data["actual"] == {"extra_columns": ["baz"], "missing_columns": ["bar"]}


def test_failing_type_eval_multi_error():
    ntype = create_structured_dataframe_type(
        "NumericType",
        columns_validator=column_validator,
        columns_aggregate_validator=aggregate_validator,
        dataframe_validator=dataframe_validator,
    )

    @op(out={"basic_dataframe": Out(dagster_type=ntype)})
    def create_dataframe(_):
        yield Output(
            DataFrame({"foo": [1, "a", 7], "baz": [9, 10, 10], "bar": [9, 10, 10]}),
            output_name="basic_dataframe",
        )

    @graph
    def basic_graph():
        return create_dataframe()

    result = basic_graph.execute_in_process(raise_on_error=False)
    output = next(item for item in result.all_node_events if item.is_successful_output)
    output_data = output.event_specific_data.type_check_data  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    output_metadata = output_data.metadata  # pyright: ignore[reportOptionalMemberAccess]
    assert len(output_metadata) == 3
    agg_data = output_metadata["column-aggregates-constraint-metadata"]
    agg_metadata = agg_data.data  # pyright: ignore[reportAttributeAccessIssue]
    assert agg_metadata["expected"] == {
        "bar": {"all_unique_validator": all_unique_validator.__doc__.strip()}  # pyright: ignore[reportOptionalMemberAccess]
    }
    assert agg_metadata["offending"] == {"bar": {"all_unique_validator": "a violation"}}
    assert agg_metadata["actual"] == {"bar": {"all_unique_validator": [10.0]}}
    column_const_data = output_metadata["columns-constraint-metadata"].data  # pyright: ignore[reportAttributeAccessIssue]
    assert column_const_data["expected"] == {
        "foo": {
            "in_range_validation_fn": in_range_validator.__doc__.strip(),  # pyright: ignore[reportOptionalMemberAccess]
            "dtype_in_set_validation_fn": dtype_is_num_validator.__doc__.strip(),  # pyright: ignore[reportOptionalMemberAccess]
        }
    }
    assert column_const_data["offending"] == {
        "foo": {
            "dtype_in_set_validation_fn": ["row 1"],
            "in_range_validation_fn": ["row 1", "row 2"],
        }
    }
    assert column_const_data["actual"] == {
        "foo": {"dtype_in_set_validation_fn": ["a"], "in_range_validation_fn": ["a", 7]}
    }

    df_metadata = output_metadata["dataframe-constraint-metadata"].data  # pyright: ignore[reportAttributeAccessIssue]
    assert df_metadata["expected"] == ["foo", "bar"]
    assert df_metadata["actual"] == {"extra_columns": ["baz"], "missing_columns": []}
