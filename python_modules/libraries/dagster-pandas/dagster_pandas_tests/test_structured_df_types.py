from dagster import DagsterType, Output, OutputDefinition, execute_pipeline, pipeline, solid
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

    @solid(output_defs=[OutputDefinition(name="basic_dataframe", dagster_type=ntype)])
    def create_dataframe(_):
        yield Output(
            DataFrame({"foo": [1, 2, 3], "bar": [9, 10, 11]}),
            output_name="basic_dataframe",
        )

    @pipeline
    def basic_pipeline():
        return create_dataframe()

    result = execute_pipeline(basic_pipeline)
    assert result.success


def test_failing_type_eval_column():
    ntype = create_structured_dataframe_type(
        "NumericType",
        columns_validator=column_validator,
        columns_aggregate_validator=aggregate_validator,
        dataframe_validator=dataframe_validator,
    )

    @solid(output_defs=[OutputDefinition(name="basic_dataframe", dagster_type=ntype)])
    def create_dataframe(_):
        yield Output(
            DataFrame({"foo": [1, "a", 7], "bar": [9, 10, 11]}),
            output_name="basic_dataframe",
        )

    @pipeline
    def basic_pipeline():
        return create_dataframe()

    result = execute_pipeline(basic_pipeline, raise_on_error=False)
    output = [item for item in result.step_event_list if item.is_successful_output][0]
    output_data = output.event_specific_data.type_check_data
    output_metadata = output_data.metadata_entries
    assert len(output_metadata) == 1
    column_const = output_metadata[0]
    assert column_const.label == "columns-constraint-metadata"
    column_const_data = column_const.entry_data.data
    assert column_const_data["expected"] == {
        "foo": {
            "in_range_validation_fn": in_range_validator.__doc__.strip(),
            "dtype_in_set_validation_fn": dtype_is_num_validator.__doc__.strip(),
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

    @solid(output_defs=[OutputDefinition(name="basic_dataframe", dagster_type=ntype)])
    def create_dataframe(_):
        yield Output(
            DataFrame({"foo": [1, 2, 3], "bar": [9, 10, 10]}),
            output_name="basic_dataframe",
        )

    @pipeline
    def basic_pipeline():
        return create_dataframe()

    result = execute_pipeline(basic_pipeline, raise_on_error=False)
    output = [item for item in result.step_event_list if item.is_successful_output][0]
    output_data = output.event_specific_data.type_check_data
    output_metadata = output_data.metadata_entries
    assert len(output_metadata) == 1
    column_const = output_metadata[0]
    assert column_const.label == "column-aggregates-constraint-metadata"
    column_const_data = column_const.entry_data.data
    assert column_const_data["expected"] == {
        "bar": {"all_unique_validator": all_unique_validator.__doc__.strip()}
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

    @solid(output_defs=[OutputDefinition(name="basic_dataframe", dagster_type=ntype)])
    def create_dataframe(_):
        yield Output(
            DataFrame({"foo": [1, 2, 3], "baz": [9, 10, 10]}),
            output_name="basic_dataframe",
        )

    @pipeline
    def basic_pipeline():
        return create_dataframe()

    result = execute_pipeline(basic_pipeline, raise_on_error=False)
    output = [item for item in result.step_event_list if item.is_successful_output][0]
    output_data = output.event_specific_data.type_check_data
    output_metadata = output_data.metadata_entries
    assert len(output_metadata) == 1
    column_const = output_metadata[0]
    assert column_const.label == "dataframe-constraint-metadata"
    column_const_data = column_const.entry_data.data
    assert column_const_data["expected"] == ["foo", "bar"]
    assert column_const_data["actual"] == {"extra_columns": ["baz"], "missing_columns": ["bar"]}


def test_failing_type_eval_multi_error():
    ntype = create_structured_dataframe_type(
        "NumericType",
        columns_validator=column_validator,
        columns_aggregate_validator=aggregate_validator,
        dataframe_validator=dataframe_validator,
    )

    @solid(output_defs=[OutputDefinition(name="basic_dataframe", dagster_type=ntype)])
    def create_dataframe(_):
        yield Output(
            DataFrame({"foo": [1, "a", 7], "baz": [9, 10, 10], "bar": [9, 10, 10]}),
            output_name="basic_dataframe",
        )

    @pipeline
    def basic_pipeline():
        return create_dataframe()

    result = execute_pipeline(basic_pipeline, raise_on_error=False)
    output = [item for item in result.step_event_list if item.is_successful_output][0]
    output_data = output.event_specific_data.type_check_data
    output_metadata = output_data.metadata_entries
    assert len(output_metadata) == 3
    agg_data = output_metadata[0]

    assert agg_data.label == "column-aggregates-constraint-metadata"
    agg_metadata = agg_data.entry_data.data
    assert agg_metadata["expected"] == {
        "bar": {"all_unique_validator": all_unique_validator.__doc__.strip()}
    }
    assert agg_metadata["offending"] == {"bar": {"all_unique_validator": "a violation"}}
    assert agg_metadata["actual"] == {"bar": {"all_unique_validator": [10.0]}}
    column_const = output_metadata[1]
    assert column_const.label == "columns-constraint-metadata"
    column_const_data = column_const.entry_data.data
    assert column_const_data["expected"] == {
        "foo": {
            "in_range_validation_fn": in_range_validator.__doc__.strip(),
            "dtype_in_set_validation_fn": dtype_is_num_validator.__doc__.strip(),
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

    df_data = output_metadata[2]
    assert df_data.label == "dataframe-constraint-metadata"
    df_metadata = df_data.entry_data.data
    assert df_metadata["expected"] == ["foo", "bar"]
    assert df_metadata["actual"] == {"extra_columns": ["baz"], "missing_columns": []}
