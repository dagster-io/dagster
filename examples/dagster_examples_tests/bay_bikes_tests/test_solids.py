# pylint: disable=redefined-outer-name
import pytest
from dagster_examples.bay_bikes.solids import MultivariateTimeseries, Timeseries
from numpy import array
from numpy.testing import assert_array_equal
from pandas import DataFrame


@pytest.fixture
def simple_timeseries():
    return Timeseries([1, 2, 3, 4, 5])


@pytest.mark.parametrize(
    'timeseries, memory_length, expected_snapshot_sequence',
    [
        (Timeseries([1, 2, 3, 4, 5]), 1, [[1, 2], [2, 3], [3, 4], [4, 5]]),
        (Timeseries([1, 2, 3, 4, 5]), 2, [[1, 2, 3], [2, 3, 4], [3, 4, 5]]),
        (Timeseries([1, 2, 3, 4, 5]), 4, [[1, 2, 3, 4, 5]]),
    ],
)
def test_timeseries_conversion_ok(timeseries, memory_length, expected_snapshot_sequence):
    assert timeseries.convert_to_snapshot_sequence(memory_length) == expected_snapshot_sequence


def test_timeseries_conversion_no_sequence():
    with pytest.raises(ValueError):
        empty_timeseries = Timeseries([])
        empty_timeseries.convert_to_snapshot_sequence(3)


@pytest.mark.parametrize('memory_length', [0, -1, 5, 6])
def test_timeseries_bad_memory_lengths(simple_timeseries, memory_length):
    with pytest.raises(ValueError):
        simple_timeseries.convert_to_snapshot_sequence(memory_length)


def test_multivariate_timeseries_transformation_ok():
    mv_timeseries = MultivariateTimeseries(
        [[1, 2, 3, 4, 5], [0, 1, 2, 3, 4]], [6, 7, 8, 9, 10], ['foo', 'bar'], 'baz'
    )
    matrix, output = mv_timeseries.convert_to_snapshot_matrix(2)
    assert_array_equal(
        matrix,
        array([[[1, 0], [2, 1], [3, 2]], [[2, 1], [3, 2], [4, 3]], [[3, 2], [4, 3], [5, 4]]]),
    )
    assert_array_equal(output, array([8, 9, 10]))


def test_mutlivariate_timeseries_transformation_from_dataframe_ok():
    mv_timeseries_df = DataFrame({'foo': [1, 2, 3], 'bar': [4, 5, 6], 'baz': [0, 0, 0]})
    mv_timeseries = MultivariateTimeseries.from_dataframe(mv_timeseries_df, ['foo', 'bar'], 'baz')
    assert mv_timeseries
    assert mv_timeseries.input_timeseries_collection[0].sequence == [1, 2, 3]
    assert mv_timeseries.input_timeseries_collection[1].sequence == [4, 5, 6]
    assert mv_timeseries.output_timeseries.sequence == [0, 0, 0]
