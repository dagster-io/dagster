import datetime
import sys
import uuid

import pandas as pd
import pytest
from dagster_gcp import (
    BigQueryError,
    bigquery_resource,
    bq_create_dataset,
    bq_delete_dataset,
    bq_solid_for_queries,
    import_df_to_bq,
    import_gcs_paths_to_bq,
)
from dagster_pandas import DataFrame
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from dagster import (
    DagsterExecutionStepExecutionError,
    InputDefinition,
    List,
    ModeDefinition,
    Nothing,
    OutputDefinition,
    Path,
    execute_pipeline,
    pipeline,
    solid,
)
from dagster.config.validate import validate_config
from dagster.core.definitions import create_environment_type
from dagster.seven import mock


def dataset_exists(name):
    '''Check if dataset exists - ensures we have properly cleaned up after tests and haven't leaked
    any datasets'''
    client = bigquery.Client()
    dataset_ref = client.dataset(name)

    try:
        client.get_dataset(dataset_ref)
        return True
    except NotFound:
        return False


def get_dataset():
    '''Creates unique dataset names of the form: test_ds_83791a53
    '''
    return 'test_ds_' + str(uuid.uuid4()).replace('-', '_')


def bq_modes():
    return [ModeDefinition(resource_defs={'bigquery': bigquery_resource})]


def test_simple_queries():
    @pipeline(mode_defs=bq_modes())
    def bq_pipeline():
        bq_solid_for_queries(
            [
                # Toy example query
                'SELECT 1 AS field1, 2 AS field2;',
                # Test access of public BQ historical dataset (only processes ~2MB here)
                # pylint: disable=line-too-long
                '''SELECT *
            FROM `weathersource-com.pub_weather_data_samples.sample_weather_history_anomaly_us_zipcode_daily`
            ORDER BY postal_code ASC, date_valid_std ASC
            LIMIT 1''',
            ]
        ).alias('bq_query_solid')()

    res = execute_pipeline(bq_pipeline).result_for_solid('bq_query_solid')
    assert res.success

    values = res.output_value()
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
            'Invalid scalar at path root:solids:test:config:query_job_config:default_dataset',
        ),
        (
            # Table must be of form project_name.dataset_name.table_name
            {'destination': 'this is not a valid table'},
            'Invalid scalar at path root:solids:test:config:query_job_config:destination',
        ),
        (
            # Priority must match enum values
            {'priority': 'this is not a valid priority'},
            'Value not in enum type BQPriority',
        ),
        (
            # Schema update options must be a list
            {'schema_update_options': 'this is not valid schema update options'},
            'Value at path root:solids:test:config:query_job_config:schema_update_options must be list. Expected: [BQSchemaUpdateOption]',
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

    @pipeline(mode_defs=bq_modes())
    def test_config_pipeline():
        bq_solid_for_queries(['SELECT 1']).alias('test')()

    env_type = create_environment_type(test_config_pipeline)
    for config_fragment, error_message in configs_and_expected_errors:
        config = {'solids': {'test': {'config': {'query_job_config': config_fragment}}}}
        result = validate_config(env_type, config)
        assert error_message in result.errors[0].message


def test_create_delete_dataset():
    dataset = get_dataset()

    @pipeline(mode_defs=bq_modes())
    def create_pipeline():
        bq_create_dataset.alias('create_solid')()

    config = {'solids': {'create_solid': {'config': {'dataset': dataset, 'exists_ok': True}}}}

    assert execute_pipeline(create_pipeline, config).result_for_solid('create_solid').success

    config = {'solids': {'create_solid': {'config': {'dataset': dataset, 'exists_ok': False}}}}
    with pytest.raises(BigQueryError) as exc_info:
        execute_pipeline(create_pipeline, config)
    assert 'Dataset "%s" already exists and exists_ok is false' % dataset in str(exc_info.value)

    @pipeline(mode_defs=bq_modes())
    def delete_pipeline():
        bq_delete_dataset.alias('delete_solid')()

    # Delete should succeed
    config = {'solids': {'delete_solid': {'config': {'dataset': dataset}}}}
    assert execute_pipeline(delete_pipeline, config).result_for_solid('delete_solid').success

    # Delete non-existent with "not_found_ok" should succeed
    config = {'solids': {'delete_solid': {'config': {'dataset': dataset, 'not_found_ok': True}}}}
    assert execute_pipeline(delete_pipeline, config).result_for_solid('delete_solid').success

    # Delete non-existent with "not_found_ok" False should fail
    config = {'solids': {'delete_solid': {'config': {'dataset': dataset, 'not_found_ok': False}}}}
    with pytest.raises(BigQueryError) as exc_info:
        execute_pipeline(delete_pipeline, config)
    assert 'Dataset "%s" does not exist and not_found_ok is false' % dataset in str(exc_info.value)

    assert not dataset_exists(dataset)


# See: https://github.com/dagster-io/dagster/issues/1711
@pytest.mark.skip
def test_pd_df_load():
    dataset = get_dataset()
    table = '%s.%s' % (dataset, 'df')

    test_df = pd.DataFrame({'num1': [1, 3], 'num2': [2, 4]})

    create_solid = bq_create_dataset.alias('create_solid')
    load_solid = import_df_to_bq.alias('load_solid')
    query_solid = bq_solid_for_queries(['SELECT num1, num2 FROM %s' % table]).alias('query_solid')
    delete_solid = bq_delete_dataset.alias('delete_solid')

    @solid(
        input_defs=[InputDefinition('success', Nothing)], output_defs=[OutputDefinition(DataFrame)]
    )
    def return_df(_context):  # pylint: disable=unused-argument
        return test_df

    config = {
        'solids': {
            'create_solid': {'config': {'dataset': dataset, 'exists_ok': True}},
            'load_solid': {'config': {'destination': table}},
            'delete_solid': {'config': {'dataset': dataset, 'delete_contents': True}},
        }
    }

    @pipeline(mode_defs=bq_modes())
    def bq_pipeline():
        delete_solid(query_solid(load_solid(return_df(create_solid()))))

    result = execute_pipeline(bq_pipeline, config)
    assert result.success

    values = result.result_for_solid('query_solid').output_value()
    assert values[0].to_dict() == test_df.to_dict()

    # BQ loads should throw an exception if pyarrow and fastparquet aren't available
    with mock.patch.dict(sys.modules, {'pyarrow': None, 'fastparquet': None}):
        with pytest.raises(DagsterExecutionStepExecutionError) as exc_info:
            result = execute_pipeline(bq_pipeline, config)
        assert (
            'loading data to BigQuery from pandas DataFrames requires either pyarrow or fastparquet'
            ' to be installed' in str(exc_info.value.user_exception)
        )
        cleanup_config = {
            'solids': {'delete_solid': {'config': {'dataset': dataset, 'delete_contents': True}}}
        }

        @pipeline(mode_defs=bq_modes())
        def cleanup():
            delete_solid()

        assert execute_pipeline(cleanup, cleanup_config).success

    assert not dataset_exists(dataset)


# See: https://github.com/dagster-io/dagster/issues/1711
@pytest.mark.skip
def test_gcs_load():
    dataset = get_dataset()
    table = '%s.%s' % (dataset, 'df')

    create_solid = bq_create_dataset.alias('create_solid')
    query_solid = bq_solid_for_queries(
        [
            'SELECT string_field_0, string_field_1 FROM %s ORDER BY string_field_0 ASC LIMIT 1'
            % table
        ]
    ).alias('query_solid')
    delete_solid = bq_delete_dataset.alias('delete_solid')

    @solid(
        input_defs=[InputDefinition('success', Nothing)], output_defs=[OutputDefinition(List[Path])]
    )
    def return_gcs_uri(_context):  # pylint: disable=unused-argument
        return ["gs://cloud-samples-data/bigquery/us-states/us-states.csv"]

    config = {
        'solids': {
            'create_solid': {'config': {'dataset': dataset, 'exists_ok': True}},
            'import_gcs_paths_to_bq': {
                'config': {
                    'destination': table,
                    'load_job_config': {
                        'autodetect': True,
                        'skip_leading_rows': 1,
                        'source_format': 'CSV',
                        'write_disposition': 'WRITE_TRUNCATE',
                    },
                }
            },
            'delete_solid': {'config': {'dataset': dataset, 'delete_contents': True}},
        }
    }

    @pipeline(mode_defs=bq_modes())
    def bq_pipeline():
        delete_solid(query_solid(import_gcs_paths_to_bq(return_gcs_uri(create_solid()))))

    result = execute_pipeline(bq_pipeline, config)
    assert result.success

    values = result.result_for_solid('query_solid').output_value()
    assert values[0].to_dict() == {'string_field_0': {0: 'Alabama'}, 'string_field_1': {0: 'AL'}}

    assert not dataset_exists(dataset)
