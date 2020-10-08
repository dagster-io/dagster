import datetime
import os

from dagster_gcp import bigquery_resource, dataproc_resource
from google.cloud.bigquery.job import LoadJobConfig, QueryJobConfig

from dagster import InputDefinition, ModeDefinition, Nothing, PresetDefinition, pipeline, solid

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DEPLOY_BUCKET_PREFIX = os.getenv("GCP_DEPLOY_BUCKET_PREFIX")
INPUT_BUCKET = os.getenv("GCP_INPUT_BUCKET")
OUTPUT_BUCKET = os.getenv("GCP_OUTPUT_BUCKET")

REGION = "us-west1"
LATEST_JAR_HASH = "214f4bff2eccb4e9c08578d96bd329409b7111c8"


@solid(required_resource_keys={"dataproc"})
def create_dataproc_cluster(context):
    context.resources.dataproc.create_cluster()


@solid(
    config_schema={"date": str},
    input_defs=[InputDefinition("start", Nothing)],
    required_resource_keys={"dataproc"},
)
def data_proc_spark_operator(context):
    dt = datetime.datetime.strptime(context.solid_config["date"], "%Y-%m-%d")

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
    job = context.resources.dataproc.submit_job(job_config)
    job_id = job["reference"]["jobId"]
    context.resources.dataproc.wait_for_job(job_id)


@solid(input_defs=[InputDefinition("start", Nothing)], required_resource_keys={"dataproc"})
def delete_dataproc_cluster(context):
    context.resources.dataproc.delete_cluster()


@solid(
    config_schema={"date": str},
    input_defs=[InputDefinition("start", Nothing)],
    required_resource_keys={"bigquery"},
)
def gcs_to_bigquery(context):
    dt = datetime.datetime.strptime(context.solid_config["date"], "%Y-%m-%d")

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

    context.resources.bigquery.load_table_from_uri(
        source_uris, destination, job_config=load_job_config
    ).result()


@solid(input_defs=[InputDefinition("start", Nothing)], required_resource_keys={"bigquery"})
def explore_visits_by_hour(context):
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
    context.resources.bigquery.query(sql, job_config=query_job_config)


@pipeline(
    mode_defs=[
        ModeDefinition(
            name="default",
            resource_defs={"bigquery": bigquery_resource, "dataproc": dataproc_resource},
        )
    ],
    preset_defs=[
        PresetDefinition.from_pkg_resources(
            "default",
            pkg_resource_defs=[
                ("dagster_examples.gcp_data_platform.environments", "resources_pipeline.yaml"),
            ],
        )
    ],
)
def gcp_data_platform():
    dataproc_job = delete_dataproc_cluster(data_proc_spark_operator(create_dataproc_cluster()))

    events_in_bq = gcs_to_bigquery(dataproc_job)
    explore_visits_by_hour(events_in_bq)
