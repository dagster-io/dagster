# pylint: disable=redefined-outer-name
import json

import pandas as pd
from dagster_examples.bay_bikes.pipelines import monthly_bay_bike_etl_pipeline

from dagster import RunConfig, execute_pipeline_with_preset


def mock_unzip_csv(zipfile_path, target):
    target = '{}/{}'.format(target, zipfile_path.split('/')[-1].replace('.zip', ''))
    mock_data = pd.DataFrame()
    mock_data.to_csv(target)
    return target


def test_download_csv_locally_pipeline(mocker):
    # Setup download mocks
    mocker.patch('dagster_examples.bay_bikes.solids.requests')
    mocker.patch('dagster_examples.bay_bikes.solids._write_chunks_to_fp')
    mocker.patch('dagster_examples.bay_bikes.solids._unzip_file', side_effect=mock_unzip_csv)

    # execute tests
    result = execute_pipeline_with_preset(
        monthly_bay_bike_etl_pipeline, preset_name='dev', run_config=RunConfig(mode='local')
    )
    assert result.success
    with open('/tmp/test_bucket/key_storage.json') as fp:
        key_storage = json.load(fp)
    assert len(key_storage.items()) == 1
