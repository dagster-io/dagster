# pylint: disable=too-many-function-args

import datetime
import os

from dagster_gcp import (
    bigquery_resource,
    bq_solid_for_queries,
    dataproc_resource,
    dataproc_solid,
    import_gcs_paths_to_bq,
)
from dagster_pandas import DataFrame

from dagster import (
    InputDefinition,
    List,
    ModeDefinition,
    Nothing,
    OutputDefinition,
    PresetDefinition,
    String,
    composite_solid,
    file_relative_path,
    pipeline,
    solid,
)

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DEPLOY_BUCKET_PREFIX = os.getenv("GCP_DEPLOY_BUCKET_PREFIX")
REGION = "us-west1"
LATEST_JAR_HASH = "214f4bff2eccb4e9c08578d96bd329409b7111c8"


@solid(
    config_schema={"paths": [str]},
    description="pass configured output paths to BigQuery load command inputs",
)
def output_paths(context, start) -> List[String]:  # pylint: disable=unused-argument
    return context.solid_config["paths"]


def events_dataproc_fn(cfg):
    dt = datetime.datetime.strptime(cfg.get("date"), "%Y-%m-%d")

    return {
        "dataproc_solid": {
            "config": {
                "job_scoped_cluster": False,
                "job_config": {
                    "job": {
                        "placement": {"clusterName": cfg.get("cluster_name")},
                        "reference": {"projectId": PROJECT_ID},
                        "sparkJob": {
                            "args": [
                                "--gcs-input-bucket",
                                cfg.get("input_bucket"),
                                "--gcs-output-bucket",
                                cfg.get("output_bucket"),
                                "--date",
                                dt.strftime("%Y-%m-%d"),
                            ],
                            "mainClass": "io.dagster.events.EventPipeline",
                            "jarFileUris": [
                                "%s/events-assembly-%s.jar"
                                % (DEPLOY_BUCKET_PREFIX, LATEST_JAR_HASH)
                            ],
                        },
                    },
                    "projectId": PROJECT_ID,
                    "region": REGION,
                },
            }
        },
        "output_paths": {
            "config": {
                "paths": [
                    "gs://{output_bucket}/{dt}/*.parquet".format(
                        output_bucket=cfg.get("output_bucket"), dt=dt.strftime("%Y/%m/%d")
                    )
                ]
            }
        },
    }


@composite_solid(
    config_fn=events_dataproc_fn,
    config_schema={"cluster_name": str, "input_bucket": str, "output_bucket": str, "date": str},
)
def events_dataproc() -> List[String]:
    return output_paths(dataproc_solid())


def bq_load_events_fn(cfg):
    dt = datetime.datetime.strptime(cfg.get("date"), "%Y-%m-%d")

    table = cfg.get("table")

    return {
        "import_gcs_paths_to_bq": {
            "config": {
                "destination": "{project_id}.{table}${date}".format(
                    project_id=PROJECT_ID, table=table, date=dt.strftime("%Y%m%d")
                ),
                "load_job_config": {
                    "source_format": "PARQUET",
                    "create_disposition": "CREATE_IF_NEEDED",
                    "write_disposition": "WRITE_TRUNCATE",
                },
            }
        }
    }


@composite_solid(
    config_fn=bq_load_events_fn,
    config_schema={"table": str, "date": str},
    output_defs=[OutputDefinition(Nothing)],
)
def bq_load_events(source_uris: List[String]):
    return import_gcs_paths_to_bq(source_uris)


def explore_visits_by_hour_fn(cfg):
    return {
        "explore_visits_by_hour_internal": {
            "config": {
                "query_job_config": {
                    "destination": "{project_id}.{table}".format(
                        project_id=PROJECT_ID, table=cfg.get("table")
                    ),
                    "create_disposition": "CREATE_IF_NEEDED",
                    "write_disposition": "WRITE_TRUNCATE",
                }
            }
        }
    }


@composite_solid(
    config_fn=explore_visits_by_hour_fn,
    config_schema={"table": str},
    input_defs=[InputDefinition("start", Nothing)],
    output_defs=[OutputDefinition(List[DataFrame])],
)
def explore_visits_by_hour(start):
    with open(file_relative_path(__file__, "sql/explore_visits_by_hour.sql"), "r") as f:
        query = f.read()

    return bq_solid_for_queries([query]).alias("explore_visits_by_hour_internal")(start=start)


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
                ("dagster_examples.gcp_data_platform.environments", "default.yaml"),
            ],
        )
    ],
)
def gcp_pipeline():
    return explore_visits_by_hour(bq_load_events(events_dataproc()))
