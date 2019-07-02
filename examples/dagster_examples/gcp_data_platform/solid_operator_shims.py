# pylint: disable=unused-argument

from dagster import composite_solid, Field, List, String

from dagster_gcp import (
    bq_load_solid_for_source,
    bq_solid_for_queries,
    dataproc_solid,
    BigQueryLoadSource,
)


def dataproc_spark_solid(
    task_id, project_id, region, cluster_name, main_class, dataproc_spark_jars, arguments
):
    def dataproc_spark_solid_fn(context, cfg):
        return {
            'dataproc_solid': {
                'config': {
                    'job_scoped_cluster': True,
                    'job_config': {
                        'job': {
                            'placement': {'clusterName': cfg['cluster_name']},
                            'reference': {'projectId': project_id},
                            'sparkJob': {
                                'args': arguments,
                                'mainClass': main_class,
                                'jarFileUris': dataproc_spark_jars,
                            },
                        },
                        'projectId': project_id,
                        'region': region,
                    },
                }
            }
        }

    @composite_solid(config_fn=dataproc_spark_solid_fn, config={'cluster_name': Field(String)})
    def dataproc_spark_solid_internal():
        return dataproc_solid()  # pylint: disable=no-value-for-parameter

    return dataproc_spark_solid_internal.alias(task_id)


def gcs_to_bigquery_solid(
    task_id,
    destination_project_dataset_table,
    source_format='CSV',
    create_disposition='CREATE_IF_NEEDED',
    write_disposition='WRITE_EMPTY',
):
    def bq_load_data_fn(context, cfg):
        return {
            'gcs_to_bigquery_solid_internal': {
                'config': {
                    'destination': destination_project_dataset_table,
                    'load_job_config': {
                        'source_format': source_format,
                        'create_disposition': create_disposition,
                        'write_disposition': write_disposition,
                    },
                }
            }
        }

    @composite_solid(config_fn=bq_load_data_fn, config={'project_id': Field(String)})
    def _gcs_to_bigquery_solid(source_uris: List[String]):
        return bq_load_solid_for_source(BigQueryLoadSource.GCS).alias(
            'gcs_to_bigquery_solid_internal'
        )(source_uris)

    return _gcs_to_bigquery_solid.alias(task_id)


def bq_sql_solid(
    task_id,
    sql,
    destination_dataset_table,
    create_disposition='CREATE_IF_NEEDED',
    write_disposition='WRITE_EMPTY',
    use_legacy_sql=False,
):
    def bq_sql_fn(context, cfg):
        return {
            'bq_sql_internal': {
                'config': {
                    'query_job_config': {
                        'destination': destination_dataset_table,
                        'create_disposition': create_disposition,
                        'write_disposition': write_disposition,
                    }
                }
            }
        }

    @composite_solid(config_fn=bq_sql_fn, config={})
    def _bq_sql_solid(start):
        return bq_solid_for_queries([sql]).alias('bq_sql_internal')(start=start)

    return _bq_sql_solid.alias(task_id)
