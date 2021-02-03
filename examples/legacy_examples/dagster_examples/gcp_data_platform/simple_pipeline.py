import datetime
import os

from dagster import InputDefinition, ModeDefinition, Nothing, pipeline, solid
from dagster_gcp.bigquery.resources import bigquery_resource
from dagster_gcp.dataproc.resources import DataprocResource
from google.cloud.bigquery.job import LoadJobConfig, QueryJobConfig

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DEPLOY_BUCKET_PREFIX = os.getenv("GCP_DEPLOY_BUCKET_PREFIX")
INPUT_BUCKET = os.getenv("GCP_INPUT_BUCKET")
OUTPUT_BUCKET = os.getenv("GCP_OUTPUT_BUCKET")

REGION = "us-west1"
LATEST_JAR_HASH = "214f4bff2eccb4e9c08578d96bd329409b7111c8"

DATAPROC_CLUSTER_CONFIG = {
    "projectId": PROJECT_ID,
    "clusterName": "gcp-data-platform",
    "region": "us-west1",
    "cluster_config": {
        "masterConfig": {"machineTypeUri": "n1-highmem-4"},
        "workerConfig": {"numInstances": 0},
        "softwareConfig": {
            "properties": {
                # Create a single-node cluster
                # This needs to be the string "true" when
                # serialized, not a boolean true
                "dataproc:dataproc.allow.zero.workers": "true"
            }
        },
    },
}


@solid
def create_dataproc_cluster(_):
    DataprocResource(DATAPROC_CLUSTER_CONFIG).create_cluster()


@solid(config_schema={"date": str}, input_defs=[InputDefinition("start", Nothing)])
def data_proc_spark_operator(context):
    dt = datetime.datetime.strptime(context.solid_config["date"], "%Y-%m-%d")

    cluster_resource = DataprocResource(DATAPROC_CLUSTER_CONFIG)
    job_config = {
        "job": {
            "placement": {"clusterName": "gcp-data-platform"},
            "reference": {"projectId": PROJECT_ID},
            "sparkJob": {
                "args": [
                    "--gcs-input-bucket",
                    INPUT_BUCKET,
                    "--gcs-output-bucket",
                    OUTPUT_BUCKET,
                    "--date",
                    dt.strftime("%Y-%m-%d"),
                ],
                "mainClass": "io.dagster.events.EventPipeline",
                "jarFileUris": [
                    "%s/events-assembly-%s.jar" % (DEPLOY_BUCKET_PREFIX, LATEST_JAR_HASH)
                ],
            },
        },
        "projectId": PROJECT_ID,
        "region": REGION,
    }
    job = cluster_resource.submit_job(job_config)
    job_id = job["reference"]["jobId"]
    cluster_resource.wait_for_job(job_id)


@solid(input_defs=[InputDefinition("start", Nothing)])
def delete_dataproc_cluster(_):
    DataprocResource(DATAPROC_CLUSTER_CONFIG).delete_cluster()


@solid(
    config_schema={"date": str},
    input_defs=[InputDefinition("start", Nothing)],
    required_resource_keys={"bigquery"},
)
def gcs_to_bigquery(context):
    dt = datetime.datetime.strptime(context.solid_config["date"], "%Y-%m-%d")
    bq = context.resources.bigquery

    destination = "{project_id}.events.events${date}".format(
        project_id=PROJECT_ID, date=dt.strftime("%Y%m%d")
    )

    load_job_config = LoadJobConfig(
        source_format="PARQUET",
        create_disposition="CREATE_IF_NEEDED",
        write_disposition="WRITE_TRUNCATE",
    )

    source_uris = [
        "gs://{bucket}/{date}/*.parquet".format(bucket=OUTPUT_BUCKET, date=dt.strftime("%Y/%m/%d"))
    ]

    bq.load_table_from_uri(source_uris, destination, job_config=load_job_config).result()


@solid(
    input_defs=[InputDefinition("start", Nothing)],
)
def explore_visits_by_hour(context):
    bq = context.resources.bigquery

    query_job_config = QueryJobConfig(
        destination="%s.aggregations.explore_visits_per_hour" % PROJECT_ID,
        create_disposition="CREATE_IF_NEEDED",
        write_disposition="WRITE_TRUNCATE",
    )

    sql = """
   SELECT FORMAT_DATETIME("%F %H:00:00", DATETIME(TIMESTAMP_SECONDS(CAST(timestamp AS INT64)))) AS ts,
          COUNT(1) AS num_visits
     FROM events.events
    WHERE url = '/explore'
 GROUP BY ts
 ORDER BY ts ASC
"""
    bq.query(sql, job_config=query_job_config)


@pipeline(mode_defs=[ModeDefinition(resource_defs={"bigquery": bigquery_resource})])
def gcp_data_platform():
    dataproc_job = delete_dataproc_cluster(data_proc_spark_operator(create_dataproc_cluster()))

    events_in_bq = gcs_to_bigquery(dataproc_job)
    explore_visits_by_hour(events_in_bq)
