from typing import Any

from dagster import (
    Bool,
    Config,
    Field as DagsterField,
    Int,
    op,
)
from dagster._annotations import beta
from dagster_shared.seven import json
from pydantic import Field

from dagster_gcp.dataproc.configs import define_dataproc_submit_job_config
from dagster_gcp.dataproc.resources import TWENTY_MINUTES, DataprocResource

# maintain the old config schema because of the nested job_config schema
DATAPROC_CONFIG_SCHEMA = {
    "job_timeout_in_seconds": DagsterField(
        Int,
        description="""Optional. Maximum time in seconds to wait for the job being
                    completed. Default is set to 1200 seconds (20 minutes).
                    """,
        is_required=False,
        default_value=TWENTY_MINUTES,
    ),
    "job_config": define_dataproc_submit_job_config(),
    "job_scoped_cluster": DagsterField(
        Bool,
        description="whether to create a cluster or use an existing cluster",
        is_required=False,
        default_value=True,
    ),
}


@beta
class DataprocOpConfig(Config):
    job_timeout_in_seconds: int = Field(
        default=TWENTY_MINUTES,
        description=(
            "Maximum time in seconds to wait for the job being completed. Default is set to 1200"
            " seconds (20 minutes)."
        ),
    )
    job_scoped_cluster: bool = Field(
        default=True,
        description="Whether to create a cluster or use an existing cluster. Defaults to True.",
    )
    project_id: str = Field(
        description=(
            "Required. Project ID for the project which the client acts on behalf of. Will be"
            " passed when creating a dataset/job."
        )
    )
    region: str = Field(description="The GCP region.")
    job_config: dict[str, Any] = Field(
        description="Python dictionary containing configuration for the Dataproc Job."
    )


def _dataproc_compute(context):
    job_config = context.op_config["job_config"]
    job_timeout = context.op_config["job_timeout_in_seconds"]

    context.log.info(
        "submitting job with config: %s and timeout of: %d seconds"  # noqa: UP031
        % (str(json.dumps(job_config)), job_timeout)
    )

    if context.op_config["job_scoped_cluster"]:
        # Cluster context manager, creates and then deletes cluster
        with context.resources.dataproc.cluster_context_manager() as cluster:
            # Submit the job specified by this solid to the cluster defined by the associated resource
            result = cluster.submit_job(job_config)

            job_id = result["reference"]["jobId"]
            context.log.info(f"Submitted job ID {job_id}")
            cluster.wait_for_job(job_id, wait_timeout=job_timeout)

    else:
        # Submit to an existing cluster
        # Submit the job specified by this solid to the cluster defined by the associated resource
        result = context.resources.dataproc.submit_job(job_config)

        job_id = result["reference"]["jobId"]
        context.log.info(f"Submitted job ID {job_id}")
        context.resources.dataproc.wait_for_job(job_id, wait_timeout=job_timeout)


@op(required_resource_keys={"dataproc"}, config_schema=DATAPROC_CONFIG_SCHEMA)
def dataproc_solid(context):
    return _dataproc_compute(context)


@op(required_resource_keys={"dataproc"}, config_schema=DATAPROC_CONFIG_SCHEMA)
@beta
def dataproc_op(context):
    return _dataproc_compute(context)


@op
@beta
def configurable_dataproc_op(context, dataproc: DataprocResource, config: DataprocOpConfig):
    job_config = {"projectId": config.project_id, "region": config.region, "job": config.job_config}
    job_timeout = config.job_timeout_in_seconds

    context.log.info(
        "submitting job with config: %s and timeout of: %d seconds"  # noqa: UP031
        % (str(json.dumps(job_config)), job_timeout)
    )

    dataproc_client = dataproc.get_client()

    if config.job_scoped_cluster:
        # Cluster context manager, creates and then deletes cluster
        with dataproc_client.cluster_context_manager() as cluster:
            # Submit the job specified by this solid to the cluster defined by the associated resource
            result = cluster.submit_job(job_config)

            job_id = result["reference"]["jobId"]
            context.log.info(f"Submitted job ID {job_id}")
            cluster.wait_for_job(job_id, wait_timeout=job_timeout)

    else:
        # Submit to an existing cluster
        # Submit the job specified by this solid to the cluster defined by the associated resource
        result = dataproc_client.submit_job(job_config)

        job_id = result["reference"]["jobId"]
        context.log.info(f"Submitted job ID {job_id}")
        dataproc_client.wait_for_job(job_id, wait_timeout=job_timeout)
