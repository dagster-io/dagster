from dagster import ResourceDefinition, build_op_context
from hacker_news.ops.id_range_for_time import (
    binary_search_nearest_left,
    binary_search_nearest_right,
    id_range_for_time,
)
from hacker_news.resources.hn_resource import hn_snapshot_client


def test_binary_search():
    arr = [2, 3, 5, 6, 7, 9, 10, 19, 30, 31]

    start = 0
    end = len(arr) - 1

    def get_value(index):
        return arr[index]

    assert binary_search_nearest_left(get_value, start, end, 20) == arr.index(30)
    assert binary_search_nearest_left(get_value, start, end, 4) == arr.index(5)
    assert binary_search_nearest_left(get_value, start, end, 5) == arr.index(5)
    assert binary_search_nearest_left(get_value, start, end, 31) == arr.index(31)
    assert binary_search_nearest_left(get_value, start, end, 32) == 10

    assert binary_search_nearest_right(get_value, start, end, 32) == arr.index(31)
    assert binary_search_nearest_right(get_value, start, end, 31) == arr.index(31)
    assert binary_search_nearest_right(get_value, start, end, 20) == arr.index(19)
    assert binary_search_nearest_right(get_value, start, end, 5) == arr.index(5)
    assert binary_search_nearest_right(get_value, start, end, 4) == arr.index(3)
    assert binary_search_nearest_right(get_value, start, end, 2) == arr.index(2)
    assert binary_search_nearest_right(get_value, start, end, 1) == None


def test_hello():
    """
    This is an example test for a Dagster op.

    For hints on how to test your Dagster ops, see our documentation tutorial on Testing:
    https://docs.dagster.io/tutorial/testable
    """
    with build_op_context(
        resources={
            "partition_start": ResourceDefinition.hardcoded_resource("2020-12-30 00:00:00"),
            "partition_end": ResourceDefinition.hardcoded_resource("2020-12-30 01:00:00"),
            "hn_client": hn_snapshot_client,
        }
    ) as context:
        id_range_for_time(context)
