import os
import time

import boto3

from dagster import (
    check,
    solid,
    Bool,
    Dict,
    Field,
    InputDefinition,
    Nothing,
    OutputDefinition,
    Path,
    Result,
    SolidDefinition,
    String,
)
from dagster.utils import safe_isfile, mkdir_p

from .configs import define_emr_run_job_flow_config
from .types import EmrClusterState, FileExistsAtPath


_START = 'start'

# wait at most 24 hours by default for cluster job completion
_DEFAULT_CLUSTER_MAX_WAIT_TIME_SEC = 24 * 60 * 60


class S3Logger(object):
    def __init__(self, logger, bucket, key, filename, size):
        self._logger = logger
        self._bucket = bucket
        self._key = key
        self._filename = filename
        self._seen_so_far = 0
        self._size = size

    def __call__(self, bytes_amount):
        self._seen_so_far += bytes_amount
        percentage = (self._seen_so_far / self._size) * 100
        self._logger(
            'Download of {bucket}/{key} to {target_file}: {percentage:.2f}% complete'.format(
                bucket=self._bucket,
                key=self._key,
                target_file=self._filename,
                percentage=percentage,
            )
        )


@solid(
    name='download_from_s3',
    config_field=Field(
        Dict(
            fields={
                'bucket': Field(String),
                'key': Field(String),
                'target_folder': Field(
                    Path, description=('Specifies the path at which to download the object.')
                ),
                'skip_if_present': Field(Bool, is_optional=True, default_value=False),
            }
        )
    ),
    description='Downloads an object from S3.',
    outputs=[OutputDefinition(FileExistsAtPath, description='The path to the downloaded object.')],
)
def download_from_s3(context):
    (bucket, key, target_folder, skip_if_present) = (
        context.solid_config.get(k) for k in ('bucket', 'key', 'target_folder', 'skip_if_present')
    )

    # file name is S3 key path suffix after last /
    target_file = os.path.join(target_folder, key.split('/')[-1])

    if skip_if_present and safe_isfile(target_file):
        context.log.info(
            'Skipping download, file already present at {target_file}'.format(
                target_file=target_file
            )
        )
    else:
        if not os.path.exists(target_folder):
            mkdir_p(target_folder)

        context.log.info(
            'Starting download of {bucket}/{key} to {target_file}'.format(
                bucket=bucket, key=key, target_file=target_file
            )
        )
        s3 = boto3.client('s3')

        headers = s3.head_object(Bucket=bucket, Key=key)
        logger = S3Logger(
            context.log.debug, bucket, key, target_file, int(headers['ContentLength'])
        )
        s3.download_file(Bucket=bucket, Key=key, Filename=target_file, Callback=logger)

    return target_file


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

        def _transform_fn(context, _):  # pylint: disable=too-many-locals
            client = boto3.client('emr')

            # kick off the EMR job flow
            response = client.run_job_flow(**context.solid_config)

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

            yield Result(job_flow_id)

        super(EmrRunJobFlowSolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=[InputDefinition(_START, Nothing)],
            outputs=[OutputDefinition(String)],
            transform_fn=_transform_fn,
            config_field=define_emr_run_job_flow_config(),
        )
