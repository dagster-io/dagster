# Portions of this file are copied from the Yelp MRJob project:
#
#   https://github.com/Yelp/mrjob
#
#
# Copyright 2009-2013 Yelp, David Marin
# Copyright 2015 Yelp
# Copyright 2017 Yelp
# Copyright 2018 Contributors
# Copyright 2019 Yelp and Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import time

import boto3
from dagster_aws.utils.mrjob.utils import _boto3_now, _wrap_aws_client, strip_microseconds

import dagster
from dagster import check

from .types import EMR_CLUSTER_TERMINATED_STATES, EmrClusterState, EmrStepState

# if we can't create or find our own service role, use the one
# created by the AWS console and CLI
_FALLBACK_SERVICE_ROLE = 'EMR_DefaultRole'

# if we can't create or find our own instance profile, use the one
# created by the AWS console and CLI
_FALLBACK_INSTANCE_PROFILE = 'EMR_EC2_DefaultRole'


class EmrJobRunner:
    def __init__(
        self, region, check_cluster_every=30, aws_access_key_id=None, aws_secret_access_key=None,
    ):
        self.region = check.str_param(region, 'region')

        # This is in seconds
        self.check_cluster_every = check.int_param(check_cluster_every, 'check_cluster_every')
        self.aws_access_key_id = check.opt_str_param(aws_access_key_id, 'aws_access_key_id')
        self.aws_secret_access_key = check.opt_str_param(
            aws_secret_access_key, 'aws_secret_access_key'
        )

    def make_emr_client(self):
        '''Creates a boto3 EMR client.
        '''
        raw_emr_client = boto3.client(
            'emr',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region,
        )
        return _wrap_aws_client(raw_emr_client, min_backoff=self.check_cluster_every)

    def add_tags(self, context, tags, cluster_id):
        '''Add tags in the dict *tags* to cluster *cluster_id*. Do nothing
        if *tags* is empty or ``None``'''
        check.opt_dict_param(tags, 'tags')
        check.str_param(cluster_id, 'cluster_id')

        if not tags:
            return

        tags_items = sorted(tags.items())

        self.make_emr_client().add_tags(
            ResourceId=cluster_id, Tags=[dict(Key=k, Value=v) for k, v in tags_items]
        )

        context.log.info(
            'Added EMR tags to cluster %s: %s'
            % (cluster_id, ', '.join('%s=%s' % (tag, value) for tag, value in tags_items))
        )

    def run_job_flow(self, context, cluster_config):
        '''Create an empty cluster on EMR, and return the ID of that job flow.
        '''
        check.dict_param(cluster_config, 'cluster_config')

        context.log.debug('Creating Elastic MapReduce cluster')
        emr_client = self.make_emr_client()

        context.log.debug(
            'Calling run_job_flow(%s)'
            % (', '.join('%s=%r' % (k, v) for k, v in sorted(cluster_config.items())))
        )
        cluster_id = emr_client.run_job_flow(**cluster_config)['JobFlowId']

        context.log.info('Created new cluster %s' % cluster_id)

        # set EMR tags for the cluster
        tags = cluster_config.get('Tags', {})
        tags['__dagster_version'] = dagster.__version__
        self.add_tags(context, tags, cluster_id)
        return cluster_id

    def describe_cluster(self, cluster_id):
        check.str_param(cluster_id, 'cluster_id')

        emr_client = self.make_emr_client()
        return emr_client.describe_cluster(ClusterId=cluster_id)['Cluster']

    def add_job_flow_steps(self, context, cluster_id, step_defs):
        '''Submit the constructed job flow steps to EMR for execution.

        Returns: list of step IDs
        '''
        check.list_param(step_defs, 'step_defs')

        emr_client = self.make_emr_client()

        steps_kwargs = dict(JobFlowId=cluster_id, Steps=step_defs)
        context.log.debug(
            'Calling add_job_flow_steps(%s)'
            % ','.join(('%s=%r' % (k, v)) for k, v in steps_kwargs.items())
        )
        return emr_client.add_job_flow_steps(**steps_kwargs)['StepIds']

    def wait_for_steps_to_complete(self, context, cluster_id, step_ids):
        '''Wait for every step of the job to complete, one by one.'''
        check.str_param(cluster_id, 'cluster_id')
        check.list_param(step_ids, 'step_ids', of_type=str)

        for step_id in step_ids:
            context.log.info('Waiting for step ID %s to complete...' % step_id)
            self._wait_for_step_to_complete(context, cluster_id, step_id)

    def _wait_for_step_to_complete(self, context, cluster_id, step_id):
        '''Helper for _wait_for_steps_to_complete(). Wait for
        step with the given ID to complete, and fetch counters.
        If it fails, attempt to diagnose the error, and raise an
        exception.
        '''
        check.str_param(cluster_id, 'cluster_id')
        check.str_param(step_id, 'step_id')

        emr_client = self.make_emr_client()

        while True:
            # don't antagonize EMR's throttling
            context.log.debug('Waiting %.1f seconds...' % self.check_cluster_every)
            time.sleep(self.check_cluster_every)

            step = emr_client.describe_step(ClusterId=cluster_id, StepId=step_id)['Step']
            step_state = EmrStepState(step['Status']['State'])

            if step_state == EmrStepState.Pending:
                cluster = self.describe_cluster(cluster_id)

                reason = _get_reason(cluster)
                reason_desc = (': %s' % reason) if reason else ''

                context.log.info(
                    'PENDING (cluster is %s%s)' % (cluster['Status']['State'], reason_desc)
                )
                continue

            elif step_state == EmrStepState.Running:
                time_running_desc = ''

                start = step['Status']['Timeline'].get('StartDateTime')
                if start:
                    time_running_desc = ' for %s' % strip_microseconds(_boto3_now() - start)

                context.log.info('RUNNING%s' % time_running_desc)
                continue

            # we're done, will return at the end of this
            elif step_state == EmrStepState.Completed:
                context.log.info('COMPLETED')
                return
            else:
                # step has failed somehow. *reason* seems to only be set
                # when job is cancelled (e.g. 'Job terminated')
                reason = _get_reason(step)
                reason_desc = (' (%s)' % reason) if reason else ''

                context.log.info('%s%s' % (step_state.value, reason_desc))

                # print cluster status; this might give more context
                # why step didn't succeed
                cluster = self.describe_cluster(cluster_id)
                reason = _get_reason(cluster)
                reason_desc = (': %s' % reason) if reason else ''
                context.log.info(
                    'Cluster %s %s %s%s'
                    % (
                        cluster['Id'],
                        'was' if 'ED' in cluster['Status']['State'] else 'is',
                        cluster['Status']['State'],
                        reason_desc,
                    )
                )

                if EmrClusterState(cluster['Status']['State']) in EMR_CLUSTER_TERMINATED_STATES:
                    # was it caused by IAM roles?
                    self._check_for_missing_default_iam_roles(context, cluster)

                    # TODO: extract logs here to surface failure reason
                    # See: https://github.com/dagster-io/dagster/issues/1954

            if step_state == EmrStepState.Failed:
                context.log.info('Step %s failed' % step_id)

            raise Exception('step failed')

    def _check_for_missing_default_iam_roles(self, context, cluster):
        '''If cluster couldn't start due to missing IAM roles, tell user what to do.'''

        reason = _get_reason(cluster)
        if any(
            reason.endswith('/%s is invalid' % role)
            for role in (_FALLBACK_INSTANCE_PROFILE, _FALLBACK_SERVICE_ROLE)
        ):
            context.log.warning(
                'IAM roles are missing. See documentation for IAM roles on EMR here: '
                'https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-iam-roles.html'
            )


def _get_reason(cluster_or_step):
    '''Get state change reason message.'''
    # StateChangeReason is {} before the first state change
    return cluster_or_step['Status']['StateChangeReason'].get('Message', '')
