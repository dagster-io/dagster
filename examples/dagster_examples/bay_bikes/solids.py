import json
import os
import zipfile
from typing import List

import pandas as pd
import requests

from dagster import Field, Float, Int, String, solid

DARK_SKY_BASE_URL = 'https://api.darksky.net/forecast'


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
    dataset = pd.concat(
        [
            pd.read_csv(
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
    pd.DataFrame(weather_report).to_csv(csv_target)
    return csv_target
