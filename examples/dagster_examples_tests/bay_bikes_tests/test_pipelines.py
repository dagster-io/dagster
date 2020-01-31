import os
from functools import partial

import pytest
from dagster_examples.bay_bikes.pipelines import monthly_trip_pipeline
from pandas import DataFrame

from dagster import execute_pipeline, seven

FAKE_ZIPFILE_NAME = 'data.csv.zip'


@pytest.fixture
def _environment_dictionary():
    return {
        'resources': {
            'postgres_db': {
                'config': {
                    'postgres_db_name': 'test',
                    'postgres_hostname': 'localhost',
                    'postgres_password': 'test',
                    'postgres_username': 'test',
                }
            },
            'volume': {'config': {'mount_location': ''}},
        },
        'solids': {
            'download_baybike_zipfile_from_url': {
                'inputs': {
                    'file_name': {'value': FAKE_ZIPFILE_NAME},
                    'base_url': {'value': 'https://foo.com'},
                }
            },
            'load_baybike_data_into_dataframe': {
                'inputs': {'target_csv_file_in_archive': {'value': '',}}
            },
            'insert_trip_data_into_table': {
                'config': {'index_label': 'uuid'},
                'inputs': {'table_name': 'test_trips'},
            },
        },
    }


@pytest.fixture
def _fake_trip_data():
    return [
        {
            'duration_sec': 68145,
            'start_time': '2019-08-31 21:27:42.2530',
            'end_time': '2019-09-01 16:23:27.4920',
            'start_station_id': 249,
            'start_station_name': 'Russell St at College Ave',
            'start_station_latitude': 37.8584732,
            'start_station_longitude': -122.2532529,
            'end_station_id': 247,
            'end_station_name': 'Fulton St at Bancroft Way',
            'end_station_latitude': 37.867789200000004,
            'end_station_longitude': -122.26589640000002,
            'bike_id': 3112,
            'user_type': 'Customer',
            'bike_share_for_all_trip': 'No',
        },
        {
            'duration_sec': 53216,
            'start_time': '2019-08-31 22:34:17.5120',
            'end_time': '2019-09-01 13:21:13.9310',
            'start_station_id': 368,
            'start_station_name': 'Myrtle St at Polk St',
            'start_station_latitude': 37.7854338279,
            'start_station_longitude': -122.41962164639999,
            'end_station_id': 78,
            'end_station_name': 'Folsom St at 9th St',
            'end_station_latitude': 37.7737172,
            'end_station_longitude': -122.41164669999999,
            'bike_id': 2440,
            'user_type': 'Customer',
            'bike_share_for_all_trip': 'No',
        },
    ]


def mock_download_zipfile(tmp_dir, fake_trip_data, _url, _target, _chunk_size):
    data_zip_file_path = os.path.join(tmp_dir, FAKE_ZIPFILE_NAME)
    DataFrame(fake_trip_data).to_csv(data_zip_file_path, compression='zip')


def test_monthly_trip_pipeline(mocker, _environment_dictionary, _fake_trip_data):
    with seven.TemporaryDirectory() as tmp_dir:
        # Run pipeline
        download_zipfile = mocker.patch(
            'dagster_examples.bay_bikes.solids._download_zipfile_from_url',
            side_effect=partial(mock_download_zipfile, tmp_dir, _fake_trip_data),
        )
        to_sql_call = mocker.patch('dagster_examples.bay_bikes.solids.DataFrame.to_sql')
        _environment_dictionary['resources']['volume']['config']['mount_location'] = tmp_dir
        # Done because we are zipping the file in the tmpdir
        _environment_dictionary['solids']['load_baybike_data_into_dataframe']['inputs'][
            'target_csv_file_in_archive'
        ]['value'] = os.path.join(tmp_dir, FAKE_ZIPFILE_NAME)
        result = execute_pipeline(monthly_trip_pipeline, environment_dict=_environment_dictionary)
        assert result.success
        download_zipfile.assert_called_with(
            'https://foo.com/data.csv.zip', os.path.join(tmp_dir, FAKE_ZIPFILE_NAME), 8192
        )
        to_sql_call.assert_called_with(
            'test_trips', mocker.ANY, if_exists='append', index=False, index_label='uuid'
        )
