import dask.dataframe as dd
import pytest
from dagster import file_relative_path, op
from dagster._core.definitions.input import In
from dagster._utils.test import wrap_op_in_graph_and_execute
from dagster_dask import DataFrame
from dagster_dask.data_frame import DataFrameReadTypes, _innermost_list2tuple
from dagster_dask.utils import DataFrameUtilities
from dask.dataframe.utils import assert_eq


def create_dask_df():
    path = file_relative_path(__file__, "num.csv")
    return dd.read_csv(path)


@pytest.mark.parametrize(
    "file_type",
    [
        pytest.param("csv", id="csv"),
        pytest.param("parquet", id="parquet"),
        pytest.param("json", id="json"),
    ],
)
def test_dataframe_inputs(file_type):
    @op(ins={"input_df": In(DataFrame)})
    def return_df(_, input_df):
        return input_df

    file_name = file_relative_path(__file__, f"num.{file_type}")

    read_result = wrap_op_in_graph_and_execute(
        return_df,
        run_config={
            "ops": {
                "return_df": {"inputs": {"input_df": {"read": {file_type: {"path": file_name}}}}}
            }
        },
        do_input_mapping=False,
    )
    assert read_result.success
    assert assert_eq(read_result.output_value(), create_dask_df())


def test_dataframe_loader_config_keys_dont_overlap():
    """Test that the read_keys, which are deprecated, do not overlap with
    the normal loader config_keys.
    """
    config_keys = set(DataFrameUtilities.keys())
    config_keys.add("read")
    read_keys = set(DataFrameReadTypes.keys())

    assert len(config_keys.intersection(read_keys)) == 0


def test_innermost_list2tuple():
    """Test that _innermost_list2tuple correctly converts filter predicates from lists to tuples.

    Parquet filters should be of the form:
    - List[Tuple[str, str, Any]] for simple filters (AND conditions)
    - List[List[Tuple[str, str, Any]]] for compound filters (OR conditions)

    YAML config converts everything to lists, so we need to convert the innermost
    list wrapping the predicate triple to a tuple.
    """
    # Test simple filter with single predicate
    input_filter = [["column", "==", "value"]]
    expected = [("column", "==", "value")]
    assert _innermost_list2tuple(input_filter) == expected

    # Test multiple simple predicates (AND condition)
    input_filter = [["column1", "==", "value1"], ["column2", ">", 100]]
    expected = [("column1", "==", "value1"), ("column2", ">", 100)]
    assert _innermost_list2tuple(input_filter) == expected

    # Test compound filter with multiple predicates (OR condition)
    input_filter = [[["column1", "==", "value1"]], [["column2", ">", 100]]]
    expected = [[("column1", "==", "value1")], [("column2", ">", 100)]]
    assert _innermost_list2tuple(input_filter) == expected

    # Test multiple predicates in same OR group (AND within OR)
    input_filter = [[["column1", "==", "value1"], ["column2", ">", 100]]]
    expected = [[("column1", "==", "value1"), ("column2", ">", 100)]]
    assert _innermost_list2tuple(input_filter) == expected

    # Test complex nested structure (OR of ANDs)
    input_filter = [
        [["col1", "==", "a"], ["col2", "<", 10]],
        [["col3", "!=", "b"]],
    ]
    expected = [
        [("col1", "==", "a"), ("col2", "<", 10)],
        [("col3", "!=", "b")],
    ]
    assert _innermost_list2tuple(input_filter) == expected


@pytest.mark.parametrize(
    "filters",
    [
        # Simple filter as it would come from YAML
        pytest.param([["num1", ">", 1]], id="simple_filter"),
        # Compound filter (OR condition) as it would come from YAML
        pytest.param([[["num1", ">", 1]], [["num2", "<", 5]]], id="compound_filter"),
    ],
)
def test_dataframe_parquet_with_filters(filters):
    """Test that parquet files can be read with filters specified in YAML format.

    This ensures that the filter conversion from lists to tuples works correctly
    in the actual dataframe loading process.
    """

    @op(ins={"input_df": In(DataFrame)})
    def return_df(_, input_df):
        return input_df

    file_name = file_relative_path(__file__, "num.parquet")

    # This should not raise an error about "too many values to unpack"
    read_result = wrap_op_in_graph_and_execute(
        return_df,
        run_config={
            "ops": {
                "return_df": {
                    "inputs": {
                        "input_df": {"read": {"parquet": {"path": file_name, "filters": filters}}}
                    }
                }
            }
        },
        do_input_mapping=False,
    )
    assert read_result.success
    # Verify we got a DataFrame back
    result_df = read_result.output_value()
    assert isinstance(result_df, dd.DataFrame)
