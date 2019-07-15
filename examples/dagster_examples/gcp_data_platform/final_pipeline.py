# pylint: disable=too-many-function-args

import datetime
import os

from dagster import (
    composite_solid,
    file_relative_path,
    pipeline,
    solid,
    Field,
    List,
    ModeDefinition,
    PresetDefinition,
    String,
)

from dagster_gcp import (
    bigquery_resource,
    bq_load_solid_for_source,
    bq_solid_for_queries,
    dataproc_resource,
    dataproc_solid,
    BigQueryLoadSource,
)

PROJECT_ID = os.getenv('GCP_PROJECT_ID')
DEPLOY_BUCKET_PREFIX = os.getenv('GCP_DEPLOY_BUCKET_PREFIX')
REGION = 'us-west1'
LATEST_JAR_HASH = '214f4bff2eccb4e9c08578d96bd329409b7111c8'


@solid(
    config={'paths': Field(List[String])},
    description='pass configured output paths to BigQuery load command inputs',
)
def output_paths(context, start) -> List[String]:  # pylint: disable=unused-argument
    return context.solid_config['paths']


def events_dataproc_fn(context, cfg):
    dt = datetime.datetime.fromtimestamp(context.run_config.tags['execution_epoch_time'])

    return {
        'dataproc_solid': {
            'config': {
                'job_scoped_cluster': False,
                'job_config': {
                    'job': {
                        'placement': {'clusterName': cfg.get('cluster_name')},
                        'reference': {'projectId': PROJECT_ID},
                        'sparkJob': {
                            'args': [
                                '--gcs-input-bucket',
                                cfg.get('input_bucket'),
                                '--gcs-output-bucket',
                                cfg.get('output_bucket'),
                                '--date',
                                dt.strftime('%Y-%m-%d'),
                            ],
                            'mainClass': 'io.dagster.events.EventPipeline',
                            'jarFileUris': [
                                '%s/events-assembly-%s.jar'
                                % (DEPLOY_BUCKET_PREFIX, LATEST_JAR_HASH)
                            ],
                        },
                    },
                    'projectId': PROJECT_ID,
                    'region': REGION,
                },
            }
        },
        'output_paths': {
            'config': {
                'paths': [
                    'gs://{output_bucket}/{dt}/*.parquet'.format(
                        output_bucket=cfg.get('output_bucket'), dt=dt.strftime('%Y/%m/%d')
                    )
                ]
            }
        },
    }


@composite_solid(
    config_fn=events_dataproc_fn,
    config={
        'cluster_name': Field(String),
        'input_bucket': Field(String),
        'output_bucket': Field(String),
    },
)
def events_dataproc() -> List[String]:
    return output_paths(dataproc_solid())  # pylint: disable=no-value-for-parameter


def bq_load_events_fn(context, cfg):
    dt = datetime.datetime.fromtimestamp(context.run_config.tags['execution_epoch_time'])

    table = cfg.get('table')

    return {
        'bq_load_events_internal': {
            'config': {
                'destination': '{project_id}.{table}${date}'.format(
                    project_id=PROJECT_ID, table=table, date=dt.strftime('%Y%m%d')
                ),
                'load_job_config': {
                    'source_format': 'PARQUET',
                    'create_disposition': 'CREATE_IF_NEEDED',
                    'write_disposition': 'WRITE_TRUNCATE',
                },
            }
        }
    }


@composite_solid(config_fn=bq_load_events_fn, config={'table': Field(String)})
def bq_load_events(source_uris: List[String]):
    return bq_load_solid_for_source(BigQueryLoadSource.GCS).alias('bq_load_events_internal')(
        source_uris
    )


def explore_visits_by_hour_fn(_, cfg):
    return {
        'explore_visits_by_hour_internal': {
            'config': {
                'query_job_config': {
                    'destination': '{project_id}.{table}'.format(
                        project_id=PROJECT_ID, table=cfg.get('table')
                    ),
                    'create_disposition': 'CREATE_IF_NEEDED',
                    'write_disposition': 'WRITE_TRUNCATE',
                }
            }
        }
    }


@composite_solid(config_fn=explore_visits_by_hour_fn, config={'table': Field(String)})
def explore_visits_by_hour(start):
    with open(file_relative_path(__file__, 'sql/explore_visits_by_hour.sql'), 'r') as f:
        query = f.read()

    return bq_solid_for_queries([query]).alias('explore_visits_by_hour_internal')(start=start)


@pipeline(
    mode_defs=[
        ModeDefinition(
            name='default', resource_defs={'bq': bigquery_resource, 'dataproc': dataproc_resource}
        )
    ],
    preset_defs=[
        PresetDefinition(
            name='default',
            mode='default',
            environment_files=[file_relative_path(__file__, 'environments/default.yaml')],
        )
    ],
)
def gcp_pipeline():
    return explore_visits_by_hour(bq_load_events(events_dataproc()))
