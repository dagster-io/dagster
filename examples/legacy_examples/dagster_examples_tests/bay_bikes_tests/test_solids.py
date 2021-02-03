# pylint: disable=redefined-outer-name, W0613
import os
import shutil
import tempfile
from datetime import date
from functools import partial

import pytest
from dagster import ModeDefinition, execute_pipeline, execute_solid, pipeline
from dagster_examples.bay_bikes.resources import credentials_vault, mount, testing_client
from dagster_examples.bay_bikes.solids import (
    MultivariateTimeseries,
    Timeseries,
    download_weather_report_from_weather_api,
    produce_training_set,
    produce_trip_dataset,
    produce_weather_dataset,
    transform_into_traffic_dataset,
    trip_etl,
    upload_pickled_object_to_gcs_bucket,
)
from dagster_examples.common.resources import postgres_db_info_resource
from dagster_examples_tests.bay_bikes_tests.test_data import FAKE_TRIP_DATA, FAKE_WEATHER_DATA
from numpy import array, array_equal
from numpy.testing import assert_array_equal
from pandas import DataFrame, Timestamp
from requests import HTTPError

START_TIME = 1514793600
VOLUME_TARGET_DIRECTORY = "/tmp/bar"
FAKE_ZIPFILE_NAME = "data.csv.zip"
BUCKET_NAME = "dagster-scratch-ccdfe1e"
TRAINING_FILE_NAME = "training_data"


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
    return MockResponse(200, {"daily": {"data": [{"time": START_TIME}]}})


@pytest.fixture
def simple_timeseries():
    return Timeseries([1, 2, 3, 4, 5])


@pytest.mark.parametrize(
    "timeseries, memory_length, expected_snapshot_sequence",
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


@pytest.mark.parametrize("memory_length", [0, -1, 5, 6])
def test_timeseries_bad_memory_lengths(simple_timeseries, memory_length):
    with pytest.raises(ValueError):
        simple_timeseries.convert_to_snapshot_sequence(memory_length)


def test_multivariate_timeseries_transformation_ok():
    mv_timeseries = MultivariateTimeseries(
        [[1, 2, 3, 4, 5], [0, 1, 2, 3, 4]], [6, 7, 8, 9, 10], ["foo", "bar"], "baz"
    )
    matrix, output = mv_timeseries.convert_to_snapshot_matrix(2)
    assert_array_equal(
        matrix,
        array([[[1, 0], [2, 1], [3, 2]], [[2, 1], [3, 2], [4, 3]], [[3, 2], [4, 3], [5, 4]]]),
    )
    assert_array_equal(output, array([8, 9, 10]))


def test_mutlivariate_timeseries_transformation_from_dataframe_ok():
    mv_timeseries_df = DataFrame({"foo": [1, 2, 3], "bar": [4, 5, 6], "baz": [0, 0, 0]})
    mv_timeseries = MultivariateTimeseries.from_dataframe(mv_timeseries_df, ["foo", "bar"], "baz")
    assert mv_timeseries
    assert mv_timeseries.input_timeseries_collection[0].sequence == [1, 2, 3]
    assert mv_timeseries.input_timeseries_collection[1].sequence == [4, 5, 6]
    assert mv_timeseries.output_timeseries.sequence == [0, 0, 0]


@pytest.fixture
def setup_dark_sky():
    old_api_key = os.environ.get("DARK_SKY_API_KEY", "")
    yield
    # pytest swallows errors and throws them in the request.node object. This is akin to a finally.
    # https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures
    os.environ["DAKR_SKY_API_KEY"] = old_api_key


def test_download_weather_report_from_weather_api_200(mocker, setup_dark_sky, mock_response_ok):
    mock_get = mocker.patch(
        "dagster_examples.bay_bikes.solids.requests.get", return_value=mock_response_ok
    )
    # Clobber api key for test so we don't expose creds
    os.environ["DARK_SKY_API_KEY"] = "uuids-will-never-collide"
    solid_result = execute_solid(
        download_weather_report_from_weather_api,
        ModeDefinition(
            resource_defs={
                "credentials_vault": credentials_vault,
            }
        ),
        run_config={
            "resources": {
                "credentials_vault": {
                    "config": {"environment_variable_names": ["DARK_SKY_API_KEY"]}
                },
            },
            "solids": {
                "download_weather_report_from_weather_api": {
                    "inputs": {"epoch_date": {"value": START_TIME}}
                }
            },
        },
    ).output_value()
    mock_get.assert_called_with(
        "https://api.darksky.net/forecast/uuids-will-never-collide/37.8267,-122.4233,1514793600?exclude=currently,minutely,hourly,alerts,flags"
    )
    assert isinstance(solid_result, DataFrame)
    assert solid_result["time"][0] == START_TIME


# pylint: disable=unused-argument
def mock_read_sql(table_name, _engine, index_col=None):
    if table_name == "weather":
        return DataFrame(FAKE_WEATHER_DATA)
    elif table_name == "trips":
        return DataFrame(FAKE_TRIP_DATA)
    return DataFrame()


def compose_training_data_env_dict():
    return {
        "resources": {
            "postgres_db": {
                "config": {
                    "db_name": "test",
                    "hostname": "localhost",
                    "password": "test",
                    "username": "test",
                }
            },
            "volume": {"config": {"mount_location": "/tmp"}},
        },
        "solids": {
            "produce_training_set": {"config": {"memory_length": 1}},
            "produce_trip_dataset": {
                "inputs": {"trip_table_name": "trips"},
            },
            "produce_weather_dataset": {
                "solids": {
                    "load_entire_weather_table": {
                        "config": {"subsets": ["time"]},
                    }
                },
                "inputs": {"weather_table_name": "weather"},
            },
            "upload_training_set_to_gcs": {
                "inputs": {
                    "bucket_name": BUCKET_NAME,
                    "file_name": TRAINING_FILE_NAME,
                }
            },
        },
    }


@pipeline(
    mode_defs=[
        ModeDefinition(
            name="testing",
            resource_defs={
                "postgres_db": postgres_db_info_resource,
                "gcs_client": testing_client,
                "volume": mount,
            },
            description="Mode to be used during testing. Allows us to clean up test artifacts without interfearing with local artifacts.",
        ),
    ],
)
def generate_test_training_set_pipeline():
    upload_training_set_to_gcs = upload_pickled_object_to_gcs_bucket.alias(
        "upload_training_set_to_gcs"
    )
    return upload_training_set_to_gcs(
        produce_training_set(
            transform_into_traffic_dataset(produce_trip_dataset()),
            produce_weather_dataset(),
        )
    )


def test_generate_training_set(mocker):
    mocker.patch("dagster_examples.bay_bikes.solids.read_sql_table", side_effect=mock_read_sql)

    # Execute Pipeline
    test_pipeline_result = execute_pipeline(
        pipeline=generate_test_training_set_pipeline,
        mode="testing",
        run_config=compose_training_data_env_dict(),
    )
    assert test_pipeline_result.success

    # Check solids
    EXPECTED_TRAFFIC_RECORDS = [
        {
            "interval_date": date(2019, 7, 31),
            "peak_traffic_load": 1,
            "time": Timestamp("2019-07-31 00:00:00"),
        },
        {
            "interval_date": date(2019, 8, 31),
            "peak_traffic_load": 1,
            "time": Timestamp("2019-08-31 00:00:00"),
        },
    ]
    traffic_dataset = test_pipeline_result.output_for_solid(
        "transform_into_traffic_dataset", output_name="traffic_dataframe"
    ).to_dict("records")
    assert all(record in EXPECTED_TRAFFIC_RECORDS for record in traffic_dataset)

    EXPECTED_WEATHER_RECORDS = [
        {
            "time": Timestamp("2019-08-31 00:00:00"),
            "summary": "Clear throughout the day.",
            "icon": "clear-day",
            "sunriseTime": 1546269960,
            "sunsetTime": 1546304520,
            "precipIntensity": 0.0007,
            "precipIntensityMax": 0.0019,
            "precipProbability": 0.05,
            "precipType": "rain",
            "temperatureHigh": 56.71,
            "temperatureHighTime": 1546294020,
            "temperatureLow": 44.75,
            "temperatureLowTime": 1546358040,
            "dewPoint": 28.34,
            "humidity": 0.43,
            "pressure": 1017.7,
            "windSpeed": 12.46,
            "windGust": 26.85,
            "windGustTime": 1546289220,
            "windBearing": 0,
            "cloudCover": 0.11,
            "uvIndex": 2,
            "uvIndexTime": 1546287180,
            "visibility": 10,
            "ozone": 314.4,
        },
        {
            "time": Timestamp("2019-07-31 00:00:00"),
            "summary": "Clear throughout the day.",
            "icon": "clear-day",
            "sunriseTime": 1546356420,
            "sunsetTime": 1546390920,
            "precipIntensity": 0.0005,
            "precipIntensityMax": 0.0016,
            "precipProbability": 0.02,
            "precipType": "sunny",
            "temperatureHigh": 55.91,
            "temperatureHighTime": 1546382040,
            "temperatureLow": 41.18,
            "temperatureLowTime": 1546437660,
            "dewPoint": 20.95,
            "humidity": 0.33,
            "pressure": 1023.3,
            "windSpeed": 6.77,
            "windGust": 22.08,
            "windGustTime": 1546343340,
            "windBearing": 22,
            "cloudCover": 0.1,
            "uvIndex": 2,
            "uvIndexTime": 1546373580,
            "visibility": 10,
            "ozone": 305.3,
        },
    ]
    weather_dataset = test_pipeline_result.output_for_solid(
        "produce_weather_dataset", output_name="weather_dataframe"
    ).to_dict("records")
    assert all(record in EXPECTED_WEATHER_RECORDS for record in weather_dataset)

    # Ensure we are generating the expected training set
    training_set, labels = test_pipeline_result.output_for_solid("produce_training_set")
    assert len(labels) == 1 and labels[0] == 1
    assert array_equal(
        training_set,
        [
            [
                [
                    1546356420.0,
                    1546390920.0,
                    0.0005,
                    0.0016,
                    0.02,
                    55.91,
                    1546382040.0,
                    41.18,
                    1546437660.0,
                    20.95,
                    0.33,
                    1023.3,
                    6.77,
                    22.08,
                    1546343340.0,
                    22.0,
                    0.1,
                    2.0,
                    1546373580.0,
                    10.0,
                    305.3,
                ],
                [
                    1546269960.0,
                    1546304520.0,
                    0.0007,
                    0.0019,
                    0.05,
                    56.71,
                    1546294020.0,
                    44.75,
                    1546358040.0,
                    28.34,
                    0.43,
                    1017.7,
                    12.46,
                    26.85,
                    1546289220.0,
                    0.0,
                    0.11,
                    2.0,
                    1546287180.0,
                    10.0,
                    314.4,
                ],
            ]
        ],
    )
    materialization_events = [
        event
        for event in test_pipeline_result.step_event_list
        if event.solid_name == "upload_training_set_to_gcs"
        and event.event_type_value == "STEP_MATERIALIZATION"
    ]
    assert len(materialization_events) == 1
    materialization = materialization_events[0].event_specific_data.materialization
    assert materialization.asset_key.path[0:5] == [
        "gs",
        "dagster",
        "scratch",
        "ccdfe1e",
        "training_data",
    ]
    materialization_event_metadata = materialization.metadata_entries
    assert len(materialization_event_metadata) == 1
    assert materialization_event_metadata[0].label == "google cloud storage URI"
    assert materialization_event_metadata[0].entry_data.text.startswith(
        "gs://dagster-scratch-ccdfe1e/training_data"
    )

    # Clean up
    shutil.rmtree(os.path.join(tempfile.gettempdir(), "testing-storage"), ignore_errors=True)


def run_config_dict():
    return {
        "resources": {
            "postgres_db": {
                "config": {
                    "db_name": "test",
                    "hostname": "localhost",
                    "password": "test",
                    "username": "test",
                }
            },
            "volume": {"config": {"mount_location": ""}},
        },
        "solids": {
            "trip_etl": {
                "solids": {
                    "download_baybike_zipfile_from_url": {
                        "inputs": {
                            "file_name": {"value": FAKE_ZIPFILE_NAME},
                            "base_url": {"value": "https://foo.com"},
                        }
                    },
                    "load_baybike_data_into_dataframe": {
                        "inputs": {
                            "target_csv_file_in_archive": {
                                "value": "",
                            }
                        }
                    },
                    "insert_trip_data_into_table": {
                        "inputs": {"table_name": "test_trips"},
                    },
                }
            }
        },
    }


def mock_download_zipfile(tmp_dir, fake_trip_data, _url, _target, _chunk_size):
    data_zip_file_path = os.path.join(tmp_dir, FAKE_ZIPFILE_NAME)
    DataFrame(fake_trip_data).to_csv(data_zip_file_path, compression="zip")


def test_monthly_trip_pipeline(mocker):
    env_dictionary = run_config_dict()
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Run pipeline
        download_zipfile = mocker.patch(
            "dagster_examples.bay_bikes.solids._download_zipfile_from_url",
            side_effect=partial(mock_download_zipfile, tmp_dir, FAKE_TRIP_DATA),
        )
        mocker.patch("dagster_examples.bay_bikes.solids._create_and_load_staging_table")
        env_dictionary["resources"]["volume"]["config"]["mount_location"] = tmp_dir
        # Done because we are zipping the file in the tmpdir
        env_dictionary["solids"]["trip_etl"]["solids"]["load_baybike_data_into_dataframe"][
            "inputs"
        ]["target_csv_file_in_archive"]["value"] = os.path.join(tmp_dir, FAKE_ZIPFILE_NAME)
        result = execute_solid(
            trip_etl,
            run_config=env_dictionary,
            mode_def=ModeDefinition(
                name="trip_testing",
                resource_defs={"postgres_db": postgres_db_info_resource, "volume": mount},
                description="Mode to be used during local demo.",
            ),
        )
        assert result.success
        download_zipfile.assert_called_with(
            "https://foo.com/data.csv.zip", os.path.join(tmp_dir, FAKE_ZIPFILE_NAME), 8192
        )
        materialization_events = result.result_for_solid(
            "insert_trip_data_into_table"
        ).materialization_events_during_compute
        assert len(materialization_events) == 1
        assert materialization_events[0].event_specific_data.materialization.label == "test_trips"
        assert (
            materialization_events[0].event_specific_data.materialization.description
            == "Table test_trips created in database test"
        )
        metadata_entries = materialization_events[
            0
        ].event_specific_data.materialization.metadata_entries
        assert len(metadata_entries) == 1
        assert metadata_entries[0].label == "num rows inserted"
        assert metadata_entries[0].entry_data.text == "2"
