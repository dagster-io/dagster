import time

import boto3

from dagster import (
    check,
    Dict,
    Field,
    InputDefinition,
    Nothing,
    OutputDefinition,
    Output,
    SolidDefinition,
    String,
)

from .configs import define_emr_run_job_flow_config
from .types import EmrClusterState


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

        def _compute_fn(context, _):  # pylint: disable=too-many-locals
            client = boto3.client('emr', region_name=context.solid_config.get('aws_region'))

            # kick off the EMR job flow
            response = client.run_job_flow(**context.solid_config['job_config'])

            # Job flow IDs and cluster IDs are interchangable
            job_flow_id = response.get('JobFlowId')

            context.log.info('waiting for EMR cluster job flow completion...')

            max_iter = max_wait_time_sec / poll_interval_sec

            # wait for the task
            done = False
            curr_iter = 0
            while not done and curr_iter < max_iter:
                cluster = client.describe_cluster(ClusterId=job_flow_id)
                status = cluster.get('Cluster', {}).get('Status', {})
                state = status.get('State')
                state_change_reason = status.get('StateChangeReason', {}).get('Message')

                context.log.info(
                    'EMR cluster %s state: %s state change reason: %s'
                    % (job_flow_id, state, state_change_reason)
                )

                # This will take a while... cluster creation usually > 5 minutes
                time.sleep(poll_interval_sec)

                # Note that the user can specify Instances.KeepJobFlowAliveWhenNoSteps, which will
                # keep the cluster alive after the job completes. In such cases where the cluster
                # continues in waiting state, we stop waiting here and yield.

                # See: https://bit.ly/2UUq1G9
                # pylint: disable=no-member
                done = state in {
                    EmrClusterState.Waiting.value,
                    EmrClusterState.Terminated.value,
                    EmrClusterState.TerminatedWithErrors.value,
                }

                curr_iter += 1

            yield Output(job_flow_id)

        super(EmrRunJobFlowSolidDefinition, self).__init__(
            name=name,
            description=description,
            input_defs=[InputDefinition(_START, Nothing)],
            output_defs=[OutputDefinition(String)],
            compute_fn=_compute_fn,
            config_field=Field(
                Dict(
                    {
                        'aws_region': Field(String, is_optional=True),
                        'job_config': define_emr_run_job_flow_config(),
                    }
                )
            ),
        )
