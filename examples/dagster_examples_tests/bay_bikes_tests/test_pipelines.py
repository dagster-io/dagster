import os
from functools import partial

from dagster_examples.bay_bikes.pipelines import monthly_trip_pipeline
from dagster_examples_tests.bay_bikes_tests.test_data import FAKE_TRIP_DATA
from pandas import DataFrame

from dagster import execute_pipeline, seven

FAKE_ZIPFILE_NAME = 'data.csv.zip'


def environment_dictionary():
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


def mock_download_zipfile(tmp_dir, fake_trip_data, _url, _target, _chunk_size):
    data_zip_file_path = os.path.join(tmp_dir, FAKE_ZIPFILE_NAME)
    DataFrame(fake_trip_data).to_csv(data_zip_file_path, compression='zip')


def test_monthly_trip_pipeline(mocker):
    env_dictionary = environment_dictionary()
    with seven.TemporaryDirectory() as tmp_dir:
        # Run pipeline
        download_zipfile = mocker.patch(
            'dagster_examples.bay_bikes.solids._download_zipfile_from_url',
            side_effect=partial(mock_download_zipfile, tmp_dir, FAKE_TRIP_DATA),
        )
        to_sql_call = mocker.patch('dagster_examples.bay_bikes.solids.DataFrame.to_sql')
        env_dictionary['resources']['volume']['config']['mount_location'] = tmp_dir
        # Done because we are zipping the file in the tmpdir
        env_dictionary['solids']['load_baybike_data_into_dataframe']['inputs'][
            'target_csv_file_in_archive'
        ]['value'] = os.path.join(tmp_dir, FAKE_ZIPFILE_NAME)
        result = execute_pipeline(monthly_trip_pipeline, environment_dict=env_dictionary)
        assert result.success
        download_zipfile.assert_called_with(
            'https://foo.com/data.csv.zip', os.path.join(tmp_dir, FAKE_ZIPFILE_NAME), 8192
        )
        to_sql_call.assert_called_with(
            'test_trips', mocker.ANY, if_exists='append', index=False, index_label='uuid'
        )
