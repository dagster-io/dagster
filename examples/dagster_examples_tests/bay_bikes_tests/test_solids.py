# pylint: disable=redefined-outer-name, W0613
import os

import pytest
from dagster_examples.bay_bikes.resources import credentials_vault
from dagster_examples.bay_bikes.solids import (
    MultivariateTimeseries,
    Timeseries,
    download_weather_report_from_weather_api,
)
from numpy import array
from numpy.testing import assert_array_equal
from pandas import DataFrame
from requests import HTTPError

from dagster import ModeDefinition, execute_solid

START_TIME = 1514793600


class MockResponse:
    def __init__(self, return_status_code, json_data):
        self.status_code = return_status_code
        self.json_data = json_data

    def raise_for_status(self):
        if self.status_code != 200:
            raise HTTPError("BAD")
        return self.status_code

    def json(self):
        return self.json_data


@pytest.fixture
def mock_response_ok():
    return MockResponse(200, {'daily': {'data': [{'time': START_TIME}]}})


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


@pytest.fixture
def setup_dark_sky():
    old_api_key = os.environ.get('DARK_SKY_API_KEY', '')
    yield
    # pytest swallows errors and throws them in the request.node object. This is akin to a finally.
    # https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures
    os.environ['DAKR_SKY_API_KEY'] = old_api_key


def test_download_weather_report_from_weather_api_200(mocker, setup_dark_sky, mock_response_ok):
    mock_get = mocker.patch(
        'dagster_examples.bay_bikes.solids.requests.get', return_value=mock_response_ok
    )
    # Clobber api key for test so we don't expose creds
    os.environ['DARK_SKY_API_KEY'] = 'uuids-will-never-collide'
    solid_result = execute_solid(
        download_weather_report_from_weather_api,
        ModeDefinition(resource_defs={'credentials_vault': credentials_vault,}),
        environment_dict={
            'resources': {
                'credentials_vault': {
                    'config': {'environment_variable_names': ['DARK_SKY_API_KEY']}
                },
            },
            'solids': {
                'download_weather_report_from_weather_api': {
                    'inputs': {'epoch_date': {'value': START_TIME}}
                }
            },
        },
    ).output_value()
    mock_get.assert_called_with(
        'https://api.darksky.net/forecast/uuids-will-never-collide/37.8267,-122.4233,1514793600?exclude=currently,minutely,hourly,alerts,flags'
    )
    assert isinstance(solid_result, DataFrame)
    assert solid_result['time'][0] == START_TIME
    assert 'uuid' in solid_result.columns
