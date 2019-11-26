import json
import os
import zipfile
from datetime import timedelta
from time import gmtime, strftime
from typing import List

import requests
from dagster_examples.bay_bikes.types import TrafficDataFrame, TripDataFrame, WeatherDataFrame
from pandas import DataFrame, concat, date_range, read_csv, to_datetime

from dagster import Field, Float, Int, String, composite_solid, solid

DARK_SKY_BASE_URL = 'https://api.darksky.net/forecast'

WEATHER_COLUMNS = [
    'time',
    'summary',
    'icon',
    'sunriseTime',
    'sunsetTime',
    'precipIntensity',
    'precipIntensityMax',
    'precipProbability',
    'precipType',
    'temperatureHigh',
    'temperatureHighTime',
    'temperatureLow',
    'temperatureLowTime',
    'dewPoint',
    'humidity',
    'pressure',
    'windSpeed',
    'windGust',
    'windGustTime',
    'windBearing',
    'cloudCover',
    'uvIndex',
    'uvIndexTime',
    'visibility',
    'ozone',
]


def _write_chunks_to_fp(response, output_fp, chunk_size):
    for chunk in response.iter_content(chunk_size=chunk_size):
        if chunk:
            output_fp.write(chunk)


def _download_zipfile_from_url(url: str, target: str, chunk_size=8192) -> str:
    with requests.get(url, stream=True) as response, open(target, 'wb+') as output_fp:
        response.raise_for_status()
        _write_chunks_to_fp(response, output_fp, chunk_size)
    return target


@solid(
    config={'chunk_size': Field(Int, is_optional=True, default_value=8192)},
    required_resource_keys={'volume'},
)
def download_zipfiles_from_urls(
    context, base_url: str, file_names: List[str], target_dir: str
) -> List[str]:
    # mount dirs onto volume
    zipfile_location = os.path.join(context.resources.volume, target_dir)
    if not os.path.exists(zipfile_location):
        os.mkdir(zipfile_location)
    for file_name in file_names:
        if not os.path.exists(os.path.join(zipfile_location, file_name)):
            _download_zipfile_from_url(
                "/".join([base_url, file_name]),
                os.path.join(zipfile_location, file_name),
                context.solid_config['chunk_size'],
            )
    return file_names


def _unzip_file(zipfile_path: str, target: str) -> str:
    with zipfile.ZipFile(zipfile_path, 'r') as zip_fp:
        zip_fp.extractall(target)
        return zip_fp.namelist()[0]


@solid(required_resource_keys={'volume'})
def unzip_files(context, file_names: List[str], source_dir: str, target_dir: str) -> List[str]:
    # mount dirs onto volume
    zipfile_location = os.path.join(context.resources.volume, source_dir)
    csv_location = os.path.join(context.resources.volume, target_dir)
    if not os.path.exists(csv_location):
        os.mkdir(csv_location)
    return [
        _unzip_file(os.path.join(zipfile_location, file_name), csv_location)
        for file_name in file_names
    ]


@solid(
    config={
        'delimiter': Field(
            String,
            default_value=',',
            is_optional=True,
            description=('A one-character string used to separate fields.'),
        )
    },
    required_resource_keys={'volume'},
)
def consolidate_csv_files(
    context, input_file_names: List[str], source_dir: str, target_name: str
) -> str:
    # mount dirs onto volume
    csv_file_location = os.path.join(context.resources.volume, source_dir)
    consolidated_csv_location = os.path.join(context.resources.volume, target_name)
    if not os.path.exists(csv_file_location):
        os.mkdir(csv_file_location)
    # There must be a header in all of these dataframes or pandas won't know how to concatinate dataframes.
    dataset = concat(
        [
            read_csv(
                os.path.join(csv_file_location, file_name),
                sep=context.solid_config['delimiter'],
                header=0,
            )
            for file_name in input_file_names
        ]
    )
    dataset.to_csv(consolidated_csv_location, sep=context.solid_config['delimiter'])
    return consolidated_csv_location


@solid(required_resource_keys={'transporter'})
def upload_file_to_bucket(context, path_to_file: str, key: str):
    context.resources.transporter.upload_file_to_bucket(path_to_file, key)


@solid(required_resource_keys={'transporter', 'volume'})
def download_csv_from_bucket_and_return_dataframe(
    context, key: str, path_to_file: str
) -> DataFrame:
    target_csv_location = os.path.join(context.resources.volume, path_to_file)
    context.resources.transporter.download_file_from_bucket(key, target_csv_location)
    return read_csv(target_csv_location)


@solid(
    config={
        'latitude': Field(
            Float,
            default_value=37.8267,
            is_optional=True,
            description=('Latitude coordinate to get weather data about. Default is SF.'),
        ),
        'longitude': Field(
            Float,
            default_value=-122.4233,
            is_optional=True,
            description=('Longitude coordinate to get weather data about. Default is SF.'),
        ),
        'times_to_exclude': Field(
            List[String],
            default_value=['currently', 'minutely', 'hourly', 'alerts', 'flags'],
            is_optional=True,
            description='data granularities to exclude when making this api call',
        ),
        'csv_name': Field(String, description=('Path to store the csv at the end')),
    },
    required_resource_keys={'credentials_vault', 'volume'},
)
def download_weather_report_from_weather_api(context, date_file_name: str) -> str:
    weather_report = []
    with open(date_file_name, 'r') as fp:
        dates = json.load(fp)
    coordinates = '{0},{1}'.format(
        context.solid_config['latitude'], context.solid_config['longitude']
    )
    weather_api_key = context.resources.credentials_vault.credentials["DARK_SKY_API_KEY"]
    url_prefix = '/'.join([DARK_SKY_BASE_URL, weather_api_key, coordinates])
    for date in dates:
        url = url_prefix + ',{}?exclude={}'.format(
            date, ','.join(context.solid_config['times_to_exclude'])
        )
        context.log.info("Download for date {}. URL is: {}".format(date, url))
        response = requests.get(url)
        response.raise_for_status()
        weather_report.append(response.json()['daily']['data'][0])
    csv_target = os.path.join(context.resources.volume, context.solid_config['csv_name'])
    DataFrame(weather_report).to_csv(csv_target)
    return csv_target


@solid
def preprocess_trip_dataset(_, dataframe: DataFrame) -> TripDataFrame:
    dataframe = dataframe[['bike_id', 'start_time', 'end_time']].dropna(how='all').reindex()
    dataframe['bike_id'] = dataframe['bike_id'].astype('int64')
    dataframe['start_time'] = to_datetime(dataframe['start_time'])
    dataframe['end_time'] = to_datetime(dataframe['end_time'])
    dataframe['interval_date'] = dataframe['start_time'].apply(lambda x: x.date())
    return TripDataFrame(dataframe)


@composite_solid
def produce_trip_dataset() -> TripDataFrame:
    download_trips_dataset = download_csv_from_bucket_and_return_dataframe.alias(
        'download_trips_dataset'
    )
    return preprocess_trip_dataset(download_trips_dataset())


@solid
def preprocess_weather_dataset(_, dataframe: DataFrame) -> WeatherDataFrame:
    '''
    Steps:

    1. Converts time columns to match the date types in the traffic dataset so
    that we can join effectively.

    2. Fills N/A values in ozone, so that we have the right datatypes.

    3. Convert precipType to a column that's more amenable to one hot encoding.
    '''
    dataframe = dataframe[WEATHER_COLUMNS].dropna(how='all').reindex()
    # These are to address weird corner cases where columns are NA
    # This fill is because the weather API fails to have a summary for certain types of clear days.
    dataframe['summary'] = dataframe['summary'].fillna('Clear throughout the day.')
    dataframe['icon'] = dataframe['icon'].fillna('clear-day')
    # This happens frequently, I defaulted to the average.
    dataframe['temperatureLow'] = dataframe['temperatureLow'].fillna(
        dataframe.temperatureLow.mean()
    )
    # This happens frequently as well, I defaulted to the median since this is a time datatype
    dataframe['temperatureLowTime'] = (
        dataframe['temperatureLowTime']
        .fillna(dataframe.temperatureLowTime.median())
        .astype('int64')
    )
    # This happens frequently, the median felt like the appropriate statistic. Can change this over time.
    dataframe['ozone'] = dataframe['ozone'].fillna(dataframe.ozone.median())
    dataframe['time'] = to_datetime(
        dataframe['time'].apply(lambda epoch_ts: strftime('%Y-%m-%d', gmtime(epoch_ts)))
    )
    dataframe['didRain'] = dataframe.precipType.apply(lambda x: x == 'rain')
    del dataframe['precipType']
    return WeatherDataFrame(dataframe)


@composite_solid
def produce_weather_dataset() -> WeatherDataFrame:
    download_weather_dataset = download_csv_from_bucket_and_return_dataframe.alias(
        'download_weather_dataset'
    )
    return preprocess_weather_dataset(download_weather_dataset())


@solid
def transform_into_traffic_dataset(_, trip_dataset: TripDataFrame) -> TrafficDataFrame:
    def max_traffic_load(trips):
        interval_count = {
            start_interval: 0 for start_interval in date_range(trips.name, periods=24, freq='h')
        }
        for interval in interval_count.keys():
            upper_bound_interval = interval + timedelta(hours=1)
            # Count number of bikes in transit during sample interval
            interval_count[interval] = len(
                trips[
                    (
                        (  # Select trip if the trip started within the sample interval
                            (interval <= trips['start_time'])
                            & (trips['start_time'] < upper_bound_interval)
                        )
                        | (  # Select trip if the trip ended within the sample interval
                            (interval <= trips['end_time'])
                            & (trips['end_time'] < upper_bound_interval)
                        )
                        | (  # Select trip if the trip started AND ended outside of the interval
                            (trips['start_time'] < interval)
                            & (trips['end_time'] >= upper_bound_interval)
                        )
                    )
                ]
            )
        return max(interval_count.values())

    counts = trip_dataset.groupby(['interval_date']).apply(max_traffic_load)
    traffic_dataset = DataFrame(counts).reset_index()
    traffic_dataset.columns = ['interval_date', 'peak_traffic_load']
    return TrafficDataFrame(traffic_dataset)
