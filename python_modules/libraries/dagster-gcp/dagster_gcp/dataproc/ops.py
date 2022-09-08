from dagster import Bool, Field, Int, op
from dagster._seven import json

from .configs import define_dataproc_submit_job_config
from .resources import TWENTY_MINUTES

DATAPROC_CONFIG_SCHEMA = {
    "job_timeout_in_seconds": Field(
        Int,
        description="""Optional. Maximum time in seconds to wait for the job being
                    completed. Default is set to 1200 seconds (20 minutes).
                    """,
        is_required=False,
        default_value=TWENTY_MINUTES,
    ),
    "job_config": define_dataproc_submit_job_config(),
    "job_scoped_cluster": Field(
        Bool,
        description="whether to create a cluster or use an existing cluster",
        is_required=False,
        default_value=True,
    ),
}


def _dataproc_compute(context):
    job_config = context.solid_config["job_config"]
    job_timeout = context.solid_config["job_timeout_in_seconds"]

    context.log.info(
        "submitting job with config: %s and timeout of: %d seconds"
        % (str(json.dumps(job_config)), job_timeout)
    )

    if context.solid_config["job_scoped_cluster"]:
        # Cluster context manager, creates and then deletes cluster
        with context.resources.dataproc.cluster_context_manager() as cluster:
            # Submit the job specified by this solid to the cluster defined by the associated resource
            result = cluster.submit_job(job_config)

            job_id = result["reference"]["jobId"]
            context.log.info("Submitted job ID {}".format(job_id))
            cluster.wait_for_job(job_id, wait_timeout=job_timeout)

    else:
        # Submit to an existing cluster
        # Submit the job specified by this solid to the cluster defined by the associated resource
        result = context.resources.dataproc.submit_job(job_config)

        job_id = result["reference"]["jobId"]
        context.log.info("Submitted job ID {}".format(job_id))
        context.resources.dataproc.wait_for_job(job_id, wait_timeout=job_timeout)


@op(required_resource_keys={"dataproc"}, config_schema=DATAPROC_CONFIG_SCHEMA)
def dataproc_solid(context):
    return _dataproc_compute(context)


@op(required_resource_keys={"dataproc"}, config_schema=DATAPROC_CONFIG_SCHEMA)
def dataproc_op(context):
    return _dataproc_compute(context)
