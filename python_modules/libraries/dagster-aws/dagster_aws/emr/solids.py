import math
import time

from dagster import (
    Field,
    InputDefinition,
    Nothing,
    Output,
    OutputDefinition,
    SolidDefinition,
    String,
    check,
)

from .configs import define_emr_run_job_flow_config
from .emr import EmrJobRunner
from .types import EMR_CLUSTER_DONE_STATES, EmrClusterState

_START = 'start'

# wait at most 24 hours by default for cluster job completion
_DEFAULT_CLUSTER_MAX_WAIT_TIME_SEC = 24 * 60 * 60


class EmrRunJobFlowSolidDefinition(SolidDefinition):
    def __init__(
        self,
        name,
        description=None,
        max_wait_time_sec=_DEFAULT_CLUSTER_MAX_WAIT_TIME_SEC,
        poll_interval_sec=5,
    ):
        name = check.str_param(name, 'name')

        description = check.opt_str_param(description, 'description', 'EMR create job flow solid.')

        def _compute_fn(context, _):

            job_runner = EmrJobRunner(region=context.solid_config.get('aws_region'))
            cluster_id = job_runner.run_job_flow(context, context.solid_config['job_config'])
            context.log.info('waiting for EMR cluster job flow completion...')

            max_iter = int(math.ceil(max_wait_time_sec / float(poll_interval_sec)))

            done = False
            curr_iter = 0
            while not done and curr_iter < max_iter:
                # This will take a while... cluster creation usually > 5 minutes
                time.sleep(poll_interval_sec)

                cluster = job_runner.describe_cluster(cluster_id)['Cluster']
                context.log.info(
                    'EMR cluster %s state: %s' % (cluster_id, cluster['Status']['State'])
                )
                done = EmrClusterState(cluster['Status']['State']) in EMR_CLUSTER_DONE_STATES
                curr_iter += 1

            yield Output(cluster_id)

        super(EmrRunJobFlowSolidDefinition, self).__init__(
            name=name,
            description=description,
            input_defs=[InputDefinition(_START, Nothing)],
            output_defs=[OutputDefinition(String)],
            compute_fn=_compute_fn,
            config={
                'aws_region': Field(String, is_required=False),
                'job_config': define_emr_run_job_flow_config(),
            },
        )
