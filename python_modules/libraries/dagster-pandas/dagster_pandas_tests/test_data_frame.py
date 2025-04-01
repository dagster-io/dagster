import pytest
from dagster import (
    DagsterInvariantViolationError,
    DagsterType,
    DynamicOutput,
    Field,
    In,
    Out,
    Output,
    Selector,
    check_dagster_type,
    dagster_type_loader,
    graph,
    job,
    op,
)
from dagster._core.definitions.metadata import MetadataValue
from dagster._utils import safe_tempfile_path
from dagster_pandas.constraints import (
    ColumnDTypeInSetConstraint,
    InRangeColumnConstraint,
    NonNullableColumnConstraint,
)
from dagster_pandas.data_frame import _execute_summary_stats, create_dagster_pandas_dataframe_type
from dagster_pandas.validation import PandasColumn
from pandas import DataFrame


def test_create_pandas_dataframe_dagster_type():
    TestDataFrame = create_dagster_pandas_dataframe_type(
        name="TestDataFrame",
        columns=[PandasColumn(name="foo", constraints=[ColumnDTypeInSetConstraint({"int64"})])],
    )
    assert isinstance(TestDataFrame, DagsterType)


def test_basic_job_with_pandas_dataframe_dagster_type():
    def compute_metadata(dataframe):
        return {"max_pid": str(max(dataframe["pid"]))}

    BasicDF = create_dagster_pandas_dataframe_type(
        name="BasicDF",
        columns=[
            PandasColumn.integer_column("pid", non_nullable=True),
            PandasColumn.string_column("names"),
        ],
        metadata_fn=compute_metadata,
    )

    @op(out={"basic_dataframe": Out(dagster_type=BasicDF)})
    def create_dataframe(_):
        yield Output(
            DataFrame({"pid": [1, 2, 3], "names": ["foo", "bar", "baz"]}),
            output_name="basic_dataframe",
        )

    @graph
    def basic_graph():
        return create_dataframe()

    result = basic_graph.execute_in_process()
    assert result.success
    for event in result.all_node_events:
        if event.event_type_value == "STEP_OUTPUT":
            mock_df_output_metadata = event.event_specific_data.type_check_data.metadata  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
            assert len(mock_df_output_metadata) == 1
            assert "max_pid" in mock_df_output_metadata


def test_create_dagster_pandas_dataframe_type_with_null_metadata_fn():
    BasicDF = create_dagster_pandas_dataframe_type(
        name="BasicDF",
        columns=[
            PandasColumn.integer_column("pid", non_nullable=True),
            PandasColumn.string_column("names"),
        ],
        metadata_fn=None,
    )
    assert isinstance(BasicDF, DagsterType)
    basic_type_check = check_dagster_type(BasicDF, DataFrame({"pid": [1], "names": ["foo"]}))
    assert basic_type_check.success


def test_bad_dataframe_type_returns_bad_stuff():
    with pytest.raises(DagsterInvariantViolationError):
        BadDFBadSummaryStats = create_dagster_pandas_dataframe_type(
            "BadDF", metadata_fn=lambda _: "ksjdkfsd"
        )
        check_dagster_type(BadDFBadSummaryStats, DataFrame({"num": [1]}))

    with pytest.raises(DagsterInvariantViolationError):
        BadDFBadSummaryStatsListItem = create_dagster_pandas_dataframe_type(
            "BadDF", metadata_fn=lambda _: ["ksjdkfsd"]
        )
        check_dagster_type(BadDFBadSummaryStatsListItem, DataFrame({"num": [1]}))


def test_dataframe_description_generation_just_type_constraint():
    TestDataFrame = create_dagster_pandas_dataframe_type(
        name="TestDataFrame",
        columns=[PandasColumn(name="foo", constraints=[ColumnDTypeInSetConstraint({"int64"})])],
    )
    assert TestDataFrame.description == "\n### Columns\n**foo**: `int64`\n\n"


def test_dataframe_description_generation_no_type_constraint():
    TestDataFrame = create_dagster_pandas_dataframe_type(
        name="TestDataFrame",
        columns=[PandasColumn(name="foo")],
    )
    assert TestDataFrame.description == "\n### Columns\n**foo**\n\n"


def test_dataframe_description_generation_multi_constraints():
    TestDataFrame = create_dagster_pandas_dataframe_type(
        name="TestDataFrame",
        columns=[
            PandasColumn(
                name="foo",
                constraints=[
                    ColumnDTypeInSetConstraint({"int64"}),
                    InRangeColumnConstraint(0, 100, ignore_missing_vals=False),
                    NonNullableColumnConstraint(),
                ],
            ),
        ],
    )
    assert (
        TestDataFrame.description
        == "\n### Columns\n**foo**: `int64`\n+ 0 < values < 100\n+ No Null values allowed.\n\n"
    )


def test_execute_summary_stats_null_function():
    assert _execute_summary_stats("foo", DataFrame(), None) == []

    metadata = _execute_summary_stats(
        "foo",
        DataFrame({"bar": [1, 2, 3]}),
        lambda value: {"qux": MetadataValue.text("baz")},
    )
    assert len(metadata) == 1
    assert metadata["qux"] == MetadataValue.text("baz")  # pyright: ignore[reportCallIssue,reportArgumentType]


def test_execute_summary_stats_error():
    with pytest.raises(DagsterInvariantViolationError):
        assert _execute_summary_stats("foo", DataFrame({}), lambda value: "jajaja")

    with pytest.raises(DagsterInvariantViolationError):
        assert _execute_summary_stats("foo", DataFrame({}), lambda value: "rofl")


def test_execute_summary_stats_metadata_value_error():
    with pytest.raises(DagsterInvariantViolationError):
        assert _execute_summary_stats("foo", DataFrame({}), lambda _: {"bad": object()})


def test_custom_dagster_dataframe_loading_ok():
    input_dataframe = DataFrame({"foo": [1, 2, 3]})
    with safe_tempfile_path() as input_csv_fp:
        input_dataframe.to_csv(input_csv_fp)
        TestDataFrame = create_dagster_pandas_dataframe_type(
            name="TestDataFrame",
            columns=[
                PandasColumn.exists("foo"),
            ],
        )

        @op(
            ins={"test_df": In(TestDataFrame)},
            out=Out(TestDataFrame),
        )
        def use_test_dataframe(_, test_df):
            assert list(test_df["foo"]) == [1, 2, 3]
            return test_df

        @graph
        def basic_graph():
            use_test_dataframe()

        result = basic_graph.execute_in_process(
            run_config={
                "ops": {
                    "use_test_dataframe": {
                        "inputs": {"test_df": {"csv": {"path": input_csv_fp}}},
                    }
                }
            }
        )
        assert result.success


def test_custom_dagster_dataframe_parametrizable_input():
    @dagster_type_loader(
        Selector(
            {
                "door_a": Field(str),
                "door_b": Field(str),
                "door_c": Field(str),
            }
        )
    )
    def silly_loader(_, config):
        which_door = next(iter(config.keys()))
        if which_door == "door_a":
            return DataFrame({"foo": ["goat"]})
        elif which_door == "door_b":
            return DataFrame({"foo": ["car"]})
        elif which_door == "door_c":
            return DataFrame({"foo": ["goat"]})
        raise DagsterInvariantViolationError(f"You did not pick a door. You chose: {which_door}")

    TestDataFrame = create_dagster_pandas_dataframe_type(
        name="TestDataFrame",
        columns=[
            PandasColumn.exists("foo"),
        ],
        loader=silly_loader,
    )

    @op(
        ins={"df": In(TestDataFrame)},
        out=Out(TestDataFrame),
    )
    def did_i_win(_, df):
        return df

    @graph
    def basic_graph():
        did_i_win()

    result = basic_graph.execute_in_process(
        run_config={
            "ops": {
                "did_i_win": {
                    "inputs": {"df": {"door_a": "bar"}},
                }
            }
        }
    )
    assert result.success
    output_df = result.output_for_node("did_i_win")
    assert isinstance(output_df, DataFrame)
    assert output_df["foo"].tolist() == ["goat"]


def test_basic_job_with_pandas_dataframe_dagster_type_metadata():
    def compute_metadata(dataframe):
        return {
            "max_pid": MetadataValue.text(str(max(dataframe["pid"]))),
        }

    BasicDF = create_dagster_pandas_dataframe_type(
        name="BasicDF",
        columns=[
            PandasColumn.integer_column("pid", non_nullable=True),
            PandasColumn.string_column("names"),
        ],
        metadata_fn=compute_metadata,
    )

    @op(out={"basic_dataframe": Out(dagster_type=BasicDF)})
    def create_dataframe(_):
        yield Output(
            DataFrame({"pid": [1, 2, 3], "names": ["foo", "bar", "baz"]}),
            output_name="basic_dataframe",
        )

    @graph
    def basic_graph():
        return create_dataframe()

    result = basic_graph.execute_in_process()
    assert result.success
    for event in result.all_node_events:
        if event.event_type_value == "STEP_OUTPUT":
            mock_df_output_metadata = event.event_specific_data.type_check_data.metadata  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
            assert len(mock_df_output_metadata) == 1
            assert "max_pid" in mock_df_output_metadata


def execute_op_in_job(the_op):
    @job
    def the_job():
        the_op()

    return the_job.execute_in_process()


def test_dataframe_annotations():
    @op
    def op_returns_dataframe() -> DataFrame:
        return DataFrame()

    assert execute_op_in_job(op_returns_dataframe).success

    @op
    def op_returns_output() -> Output[DataFrame]:
        return Output(DataFrame())

    assert execute_op_in_job(op_returns_output).success

    @op
    def op_returns_dynamic_output() -> list[DynamicOutput[DataFrame]]:
        return [DynamicOutput(DataFrame(), "1")]

    assert execute_op_in_job(op_returns_dynamic_output).success
