# pylint: disable=too-many-function-args, no-value-for-parameter

import os

from dagster import pipeline, solid, List, ModeDefinition, String

from dagster_gcp import bigquery_resource, dataproc_resource

from .solid_operator_shims import bq_sql_solid, dataproc_spark_solid, gcs_to_bigquery_solid

PROJECT_ID = os.getenv('GCP_PROJECT_ID')
DEPLOY_BUCKET_PREFIX = os.getenv('GCP_DEPLOY_BUCKET_PREFIX')
INPUT_BUCKET = os.getenv('GCP_INPUT_BUCKET')
OUTPUT_BUCKET = os.getenv('GCP_OUTPUT_BUCKET')

REGION = 'us-west1'
LATEST_JAR_HASH = '214f4bff2eccb4e9c08578d96bd329409b7111c8'


@solid(description='pass configured output paths to BigQuery load command inputs')
def output_paths(context, start) -> List[String]:  # pylint: disable=unused-argument
    return ['gs://acme-co-events-output-dev/{{ ds_as_path }}/*.parquet']  # TODO: can't do this


@pipeline(
    mode_defs=[
        ModeDefinition(resource_defs={'bq': bigquery_resource, 'dataproc': dataproc_resource})
    ]
)
def gcp_pipeline():
    # create_dataproc_cluster
    # (not needed) This is configured and managed by Dagster's resource system
    #

    run_dataproc_spark = dataproc_spark_solid(
        task_id='events_dataproc',
        project_id=PROJECT_ID,
        cluster_name='gcp-data-platform',
        region=REGION,
        main_class='io.dagster.events.EventPipeline',
        dataproc_spark_jars=['%s/events-assembly-%s.jar' % (DEPLOY_BUCKET_PREFIX, LATEST_JAR_HASH)],
        arguments=[
            '--gcs-input-bucket',
            INPUT_BUCKET,
            '--gcs-output-bucket',
            OUTPUT_BUCKET,
            '--date',
            '{{ ds }}',  # this still won't work b/c Airflow won't template stuff deep in Dagster
        ],
    )

    # delete_dataproc_cluster
    # (not needed) This is managed by Dagster's resource system

    gcs_to_bigquery = gcs_to_bigquery_solid(
        task_id='gcs_to_bigquery',
        # bucket: Don't need to provide bucket
        # source_objects: provided by solid input from output_paths
        destination_project_dataset_table='{project_id}.events.events{{ ds_nodash }}'.format(
            project_id=PROJECT_ID
        ),
        source_format='PARQUET',
        create_disposition='CREATE_IF_NEEDED',
        write_disposition='WRITE_TRUNCATE',
    )

    explore_visits_by_hour = bq_sql_solid(
        task_id='explore_visits_by_hour',
        sql='''
   SELECT FORMAT_DATETIME("%F %H:00:00", DATETIME(TIMESTAMP_SECONDS(CAST(timestamp AS INT64)))) AS ts,
          COUNT(1) AS num_visits
     FROM events.events
    WHERE url = '/explore'
 GROUP BY ts
 ORDER BY ts ASC
 ''',
        destination_dataset_table='aggregations.explore_visits_per_hour',
        create_disposition='CREATE_IF_NEEDED',
        write_disposition='WRITE_TRUNCATE',
        use_legacy_sql=False,
    )

    loaded_events = gcs_to_bigquery(output_paths(run_dataproc_spark()))
    return explore_visits_by_hour(loaded_events)
