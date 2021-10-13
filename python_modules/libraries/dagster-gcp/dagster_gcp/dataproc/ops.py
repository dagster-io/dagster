from dagster import Bool, Field, op, solid
from dagster.seven import json

from .configs import define_dataproc_submit_job_config

DATAPROC_CONFIG_SCHEMA = {
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

    context.log.info("submitting job with config: %s" % str(json.dumps(job_config)))

    if context.solid_config["job_scoped_cluster"]:
        # Cluster context manager, creates and then deletes cluster
        with context.resources.dataproc.cluster_context_manager() as cluster:
            # Submit the job specified by this solid to the cluster defined by the associated resource
            result = cluster.submit_job(job_config)

            job_id = result["reference"]["jobId"]
            context.log.info("Submitted job ID {}".format(job_id))
            cluster.wait_for_job(job_id)
    else:
        # Submit to an existing cluster
        # Submit the job specified by this solid to the cluster defined by the associated resource
        result = context.resources.dataproc.submit_job(job_config)

        job_id = result["reference"]["jobId"]
        context.log.info("Submitted job ID {}".format(job_id))
        context.resources.dataproc.wait_for_job(job_id)


@solid(required_resource_keys={"dataproc"}, config_schema=DATAPROC_CONFIG_SCHEMA)
def dataproc_solid(context):
    return _dataproc_compute(context)


@op(required_resource_keys={"dataproc"}, config_schema=DATAPROC_CONFIG_SCHEMA)
def dataproc_op(context):
    return _dataproc_compute(context)
