from dagster import solid

from .configs import define_dataproc_submit_job_config


@solid(resources={'dataproc'}, config_field=define_dataproc_submit_job_config())
def dataproc_solid(context):
    # Cluster context manager, creates and then deletes cluster
    with context.resources.dataproc.cluster_context_manager() as cluster:
        # Submit the job specified by this solid to the cluster defined by the associated resource
        result = cluster.submit_job(context.solid_config)

        job_id = result['reference']['jobId']
        context.log.info('Submitted job ID {}'.format(job_id))
        cluster.wait_for_job(job_id)
