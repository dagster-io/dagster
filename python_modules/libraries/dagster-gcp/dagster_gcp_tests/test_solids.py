import datetime
import pytest

import pandas as pd

from dagster import PipelineConfigEvaluationError, PipelineDefinition, execute_pipeline

from dagster_gcp import BigQuerySolidDefinition


def test_simple_queries():
    solid_inst = BigQuerySolidDefinition(
        'test',
        [
            # Toy example query
            'SELECT 1 AS field1, 2 AS field2;',
            # Test access of public BQ historical dataset (only processes ~2MB here)
            # pylint: disable=line-too-long
            '''SELECT *
            FROM `weathersource-com.pub_weather_data_samples.sample_weather_history_anomaly_us_zipcode_daily`
            ORDER BY postal_code ASC, date_valid_std ASC
            LIMIT 1''',
        ],
    )

    pipeline = PipelineDefinition(solids=[solid_inst])
    pipeline_result = execute_pipeline(pipeline)
    res = pipeline_result.result_for_solid(solid_inst.name)
    assert res.success

    values = res.transformed_value()
    for df in values:
        assert isinstance(df, pd.DataFrame)
    assert values[0].to_dict('list') == {'field1': [1], 'field2': [2]}
    assert values[1].to_dict('list') == {
        'postal_code': ['02101'],
        'country': ['US'],
        'date_valid_std': [datetime.date(2014, 1, 1)],
        'doy_std': [1],
        'avg_temperature_air_2m_f': [25.05],
        'avg_temperature_anomaly_air_2m_f': [-7.81],
        'tot_precipitation_in': [0.0],
        'tot_precipitation_anomaly_in': [-0.28],
        'tot_snowfall_in': [0.0],
        'tot_snowfall_anomaly_in': [-1.36],
        'avg_wind_speed_10m_mph': [7.91],
        'avg_wind_speed_10m_anomaly_mph': [-1.85],
    }


def test_bad_config():
    solid_inst = BigQuerySolidDefinition('test', ['SELECT 1'])
    pipeline_def = PipelineDefinition(name='test_config_pipeline', solids=[solid_inst])

    bad_create_disposition = {
        'solids': {'test': {'config': {'create_disposition': 'bad config - not CREATE_IF_NEEDED'}}}
    }

    bad_default_dataset = {
        'solids': {'test': {'config': {'default_dataset': 'not a valid dataset'}}}
    }

    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(pipeline_def, bad_create_disposition)
        assert (
            'Error 1: Type failure at path "root:solids:test:config:create_disposition" on type "BQCreateDisposition". Value not in enum type BQCreateDisposition.'
            in str(exc_info.value)
        )

    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(pipeline_def, bad_default_dataset)
        assert (
            'Error 1: Type failure at path "root:solids:test:config:default_dataset" on type "BQDataset". Value at path root:solids:test:config:default_dataset is not valid. Expected "BQDataset"'
            in str(exc_info.value)
        )

