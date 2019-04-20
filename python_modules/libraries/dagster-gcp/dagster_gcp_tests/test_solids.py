import datetime
import pandas as pd

from dagster import PipelineDefinition, execute_pipeline
from dagster.core.types.evaluator import evaluate_config_value

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


# pylint: disable=line-too-long
def test_bad_config():
    configs_and_expected_errors = [
        (
            # Create disposition must match enum values
            {'create_disposition': 'this is not a valid create disposition'},
            'Value not in enum type BQCreateDisposition',
        ),
        (
            # Dataset must be of form project_name.dataset_name
            {'default_dataset': 'this is not a valid dataset'},
            'Value at path root:solids:test:config:default_dataset is not valid. Expected "Dataset"',
        ),
        (
            # Table must be of form project_name.dataset_name.table_name
            {'destination': 'this is not a valid table'},
            'Value at path root:solids:test:config:destination is not valid. Expected "Table"',
        ),
        (
            # Priority must match enum values
            {'priority': 'this is not a valid priority'},
            'Value not in enum type BQPriority',
        ),
        (
            # Schema update options must be a list
            {'schema_update_options': 'this is not valid schema update options'},
            'Value at path root:solids:test:config:schema_update_options must be list. Expected: [BQSchemaUpdateOption]',
        ),
        (
            {'schema_update_options': ['this is not valid schema update options']},
            'Value not in enum type BQSchemaUpdateOption',
        ),
        (
            {'write_disposition': 'this is not a valid write disposition'},
            'Value not in enum type BQWriteDisposition',
        ),
    ]

    pipeline_def = PipelineDefinition(
        name='test_config_pipeline', solids=[BigQuerySolidDefinition('test', ['SELECT 1'])]
    )

    for config_fragment, error_message in configs_and_expected_errors:
        config = {'solids': {'test': {'config': config_fragment}}}
        result = evaluate_config_value(pipeline_def.environment_type, config)
        assert result.errors[0].message == error_message
