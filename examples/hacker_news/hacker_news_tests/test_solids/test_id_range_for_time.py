from dagster import execute_solid
from hacker_news.pipelines.download_pipeline import MODE_TEST
from hacker_news.solids.id_range_for_time import (
    binary_search_nearest_left,
    binary_search_nearest_right,
    id_range_for_time,
)


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
    This is an example test for a Dagster solid.

    For hints on how to test your Dagster solids, see our documentation tutorial on Testing:
    https://docs.dagster.io/tutorial/testable
    """
    result = execute_solid(
        id_range_for_time,
        run_config={
            "resources": {
                "partition_start": {"config": "2020-12-30 00:00:00"},
                "partition_end": {"config": "2020-12-30 01:00:00"},
            },
        },
        mode_def=MODE_TEST,
    )

    assert result.success
