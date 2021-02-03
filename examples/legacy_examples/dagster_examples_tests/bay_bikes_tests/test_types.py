from datetime import timedelta

import pytest
from dagster import check_dagster_type
from dagster_examples.bay_bikes.types import TrainingSet, TripDataFrame, WeatherDataFrame
from numpy import array
from pandas import DataFrame, Timestamp


def valid_trip_dataframe():
    start_date = Timestamp(year=2018, month=2, day=1)
    start_dates = [start_date, start_date + timedelta(weeks=1), start_date + timedelta(weeks=2)]
    return DataFrame(
        {
            "bike_id": [1, 2, 3],
            "start_time": start_dates,
            "end_time": [dt + timedelta(days=1) for dt in start_dates],
            "interval_date": [dt.strftime("%Y-%m-%d") for dt in start_dates],
        }
    )


def valid_weather_dataframe():
    return DataFrame(
        [
            {
                "time": Timestamp("2019-06-24 00:00:00"),
                "summary": "Partly cloudy throughout the day.",
                "icon": "partly-cloudy-day",
                "sunriseTime": 1561380600,
                "sunsetTime": 1561433820,
                "precipIntensity": 0.0,
                "precipIntensityMax": 0.0001,
                "precipIntensityMaxTime": 1561391400.0,
                "precipProbability": 0.05,
                "temperatureHigh": 68.97,
                "temperatureHighTime": 1561410180,
                "temperatureLow": 56.42,
                "temperatureLowTime": 1561468380.0,
                "dewPoint": 56.98,
                "humidity": 0.88,
                "pressure": 1011.1,
                "windSpeed": 6.64,
                "windGust": 12.91,
                "windGustTime": 1561417560,
                "windBearing": 251,
                "cloudCover": 0.45,
                "uvIndex": 7,
                "uvIndexTime": 1561404420,
                "visibility": 7.723,
                "ozone": 333.6,
                "did_rain": False,
            }
        ]
    )


def valid_training_set():
    X = array([[[1, 2], [2, 3]], [[4, 5], [5, 6]]])
    y = array([3, 4])
    return (X, y)


def missing_column_dataframe():
    df = valid_trip_dataframe()
    return df[["bike_id", "start_time", "end_time"]]


def bad_dtype_df():
    df = valid_trip_dataframe()
    df["start_time"] = ["foo", "bar", "baz"]
    return df


def test_validate_dataframe_ok():
    assert check_dagster_type(TripDataFrame, valid_trip_dataframe()).success


@pytest.mark.parametrize("invalid_dataframe", [missing_column_dataframe(), bad_dtype_df()])
def test_validate_dataframe_missing_column(invalid_dataframe):
    assert not check_dagster_type(TripDataFrame, invalid_dataframe).success


def test_validate_dataframe_invalid_categories():
    df = valid_weather_dataframe()
    df["icon"][0] = "foo"
    assert not check_dagster_type(WeatherDataFrame, df).success


def test_validate_training_data_ok():
    data = valid_training_set()
    assert check_dagster_type(TrainingSet, data).success


@pytest.mark.parametrize(
    "bad_training_data",
    [
        (array([[[]], [[]]]), array([])),
        (array([[[1, 2], [2, 3]], [[4, 5], [5, 6]]]), array([3])),
    ],
)
def test_validate_training_data_failure(bad_training_data):
    assert not check_dagster_type(TrainingSet, bad_training_data).success
