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
import gzip
import re
from io import BytesIO
from urllib.parse import urlparse

import boto3
import dagster
from botocore.exceptions import WaiterError
from dagster import check
from dagster_aws.utils.mrjob.utils import _boto3_now, _wrap_aws_client, strip_microseconds

from .types import EMR_CLUSTER_TERMINATED_STATES, EmrClusterState, EmrStepState

# if we can't create or find our own service role, use the one
# created by the AWS console and CLI
_FALLBACK_SERVICE_ROLE = "EMR_DefaultRole"

# if we can't create or find our own instance profile, use the one
# created by the AWS console and CLI
_FALLBACK_INSTANCE_PROFILE = "EMR_EC2_DefaultRole"


class EmrError(Exception):
    pass


class EmrJobRunner:
    def __init__(
        self,
        region,
        check_cluster_every=30,
        aws_access_key_id=None,
        aws_secret_access_key=None,
    ):
        """This object encapsulates various utilities for interacting with EMR clusters and invoking
        steps (jobs) on them.

        See also :py:class:`~dagster_aws.emr.EmrPySparkResource`, which wraps this job runner in a
        resource for pyspark workloads.

        Args:
            region (str): AWS region to use
            check_cluster_every (int, optional): How frequently to poll boto3 APIs for updates.
                Defaults to 30 seconds.
            aws_access_key_id ([type], optional): AWS access key ID. Defaults to None, which will
                use the default boto3 credentials chain.
            aws_secret_access_key ([type], optional): AWS secret access key. Defaults to None, which
                will use the default boto3 credentials chain.
        """
        self.region = check.str_param(region, "region")

        # This is in seconds
        self.check_cluster_every = check.int_param(check_cluster_every, "check_cluster_every")
        self.aws_access_key_id = check.opt_str_param(aws_access_key_id, "aws_access_key_id")
        self.aws_secret_access_key = check.opt_str_param(
            aws_secret_access_key, "aws_secret_access_key"
        )

    def make_emr_client(self):
        """Creates a boto3 EMR client. Construction is wrapped in retries in case client connection
        fails transiently.

        Returns:
            botocore.client.EMR: An EMR client
        """
        raw_emr_client = boto3.client(
            "emr",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region,
        )
        return _wrap_aws_client(raw_emr_client, min_backoff=self.check_cluster_every)

    def cluster_id_from_name(self, cluster_name):
        """Get a cluster ID in the format "j-123ABC123ABC1" given a cluster name "my cool cluster".

        Args:
            cluster_name (str): The name of the cluster for which to find an ID

        Returns:
            str: The ID of the cluster

        Raises:
            EmrError: No cluster with the specified name exists
        """
        check.str_param(cluster_name, "cluster_name")

        response = self.make_emr_client().list_clusters().get("Clusters", [])
        for cluster in response:
            if cluster["Name"] == cluster_name:
                return cluster["Id"]

        raise EmrError(
            "cluster {cluster_name} not found in region {region}".format(
                cluster_name=cluster_name, region=self.region
            )
        )

    @staticmethod
    def construct_step_dict_for_command(step_name, command, action_on_failure="CONTINUE"):
        """Construct an EMR step definition which uses command-runner.jar to execute a shell command
        on the EMR master.

        Args:
            step_name (str): The name of the EMR step (will show up in the EMR UI)
            command (str): The shell command to execute with command-runner.jar
            action_on_failure (str, optional): Configure action on failure (e.g., continue, or
                terminate the cluster). Defaults to 'CONTINUE'.

        Returns:
            dict: Step definition dict
        """
        check.str_param(step_name, "step_name")
        check.list_param(command, "command", of_type=str)
        check.str_param(action_on_failure, "action_on_failure")

        return {
            "Name": step_name,
            "ActionOnFailure": action_on_failure,
            "HadoopJarStep": {"Jar": "command-runner.jar", "Args": command},
        }

    def add_tags(self, log, tags, cluster_id):
        """Add tags in the dict tags to cluster cluster_id.

        Args:
            log (DagsterLogManager): Log manager, for logging
            tags (dict): Dictionary of {'key': 'value'} tags
            cluster_id (str): The ID of the cluster to tag
        """
        check.dict_param(tags, "tags")
        check.str_param(cluster_id, "cluster_id")

        tags_items = sorted(tags.items())

        self.make_emr_client().add_tags(
            ResourceId=cluster_id, Tags=[dict(Key=k, Value=v) for k, v in tags_items]
        )

        log.info(
            "Added EMR tags to cluster %s: %s"
            % (cluster_id, ", ".join("%s=%s" % (tag, value) for tag, value in tags_items))
        )

    def run_job_flow(self, log, cluster_config):
        """Create an empty cluster on EMR, and return the ID of that job flow.

        Args:
            log (DagsterLogManager): Log manager, for logging
            cluster_config (dict): Configuration for this EMR job flow. See:
                https://docs.aws.amazon.com/emr/latest/APIReference/API_RunJobFlow.html

        Returns:
            str: The cluster ID, e.g. "j-ZKIY4CKQRX72"
        """
        check.dict_param(cluster_config, "cluster_config")

        log.debug("Creating Elastic MapReduce cluster")
        emr_client = self.make_emr_client()

        log.debug(
            "Calling run_job_flow(%s)"
            % (", ".join("%s=%r" % (k, v) for k, v in sorted(cluster_config.items())))
        )
        cluster_id = emr_client.run_job_flow(**cluster_config)["JobFlowId"]

        log.info("Created new cluster %s" % cluster_id)

        # set EMR tags for the cluster
        tags = cluster_config.get("Tags", {})
        tags["__dagster_version"] = dagster.__version__
        self.add_tags(log, tags, cluster_id)
        return cluster_id

    def describe_cluster(self, cluster_id):
        """Thin wrapper over boto3 describe_cluster.

        Args:
            cluster_id (str): Cluster to inspect

        Returns:
            dict: The cluster info. See:
                https://docs.aws.amazon.com/emr/latest/APIReference/API_DescribeCluster.html
        """
        check.str_param(cluster_id, "cluster_id")

        emr_client = self.make_emr_client()
        return emr_client.describe_cluster(ClusterId=cluster_id)

    def describe_step(self, cluster_id, step_id):
        """Thin wrapper over boto3 describe_step.

        Args:
            cluster_id (str): Cluster to inspect
            step_id (str): Step ID to describe

        Returns:
            dict: The step info. See:
                https://docs.aws.amazon.com/emr/latest/APIReference/API_DescribeStep.html
        """
        check.str_param(cluster_id, "cluster_id")
        check.str_param(step_id, "step_id")

        emr_client = self.make_emr_client()
        return emr_client.describe_step(ClusterId=cluster_id, StepId=step_id)

    def add_job_flow_steps(self, log, cluster_id, step_defs):
        """Submit the constructed job flow steps to EMR for execution.

        Args:
            log (DagsterLogManager): Log manager, for logging
            cluster_id (str): The ID of the cluster
            step_defs (List[dict]): List of steps; see also `construct_step_dict_for_command`

        Returns:
            List[str]: list of step IDs.
        """
        check.str_param(cluster_id, "cluster_id")
        check.list_param(step_defs, "step_defs", of_type=dict)

        emr_client = self.make_emr_client()

        steps_kwargs = dict(JobFlowId=cluster_id, Steps=step_defs)
        log.debug(
            "Calling add_job_flow_steps(%s)"
            % ",".join(("%s=%r" % (k, v)) for k, v in steps_kwargs.items())
        )
        return emr_client.add_job_flow_steps(**steps_kwargs)["StepIds"]

    def is_emr_step_complete(self, log, cluster_id, emr_step_id):
        step = self.describe_step(cluster_id, emr_step_id)["Step"]
        step_state = EmrStepState(step["Status"]["State"])

        if step_state == EmrStepState.Pending:
            cluster = self.describe_cluster(cluster_id)["Cluster"]

            reason = _get_reason(cluster)
            reason_desc = (": %s" % reason) if reason else ""

            log.info("PENDING (cluster is %s%s)" % (cluster["Status"]["State"], reason_desc))
            return False

        elif step_state == EmrStepState.Running:
            time_running_desc = ""

            start = step["Status"]["Timeline"].get("StartDateTime")
            if start:
                time_running_desc = " for %s" % strip_microseconds(_boto3_now() - start)

            log.info("RUNNING%s" % time_running_desc)
            return False

        # we're done, will return at the end of this
        elif step_state == EmrStepState.Completed:
            log.info("COMPLETED")
            return True
        else:
            # step has failed somehow. *reason* seems to only be set
            # when job is cancelled (e.g. 'Job terminated')
            reason = _get_reason(step)
            reason_desc = (" (%s)" % reason) if reason else ""

            log.info("%s%s" % (step_state.value, reason_desc))

            # print cluster status; this might give more context
            # why step didn't succeed
            cluster = self.describe_cluster(cluster_id)["Cluster"]
            reason = _get_reason(cluster)
            reason_desc = (": %s" % reason) if reason else ""
            log.info(
                "Cluster %s %s %s%s"
                % (
                    cluster["Id"],
                    "was" if "ED" in cluster["Status"]["State"] else "is",
                    cluster["Status"]["State"],
                    reason_desc,
                )
            )

            if EmrClusterState(cluster["Status"]["State"]) in EMR_CLUSTER_TERMINATED_STATES:
                # was it caused by IAM roles?
                self._check_for_missing_default_iam_roles(log, cluster)

                # TODO: extract logs here to surface failure reason
                # See: https://github.com/dagster-io/dagster/issues/1954

        if step_state == EmrStepState.Failed:
            log.error("EMR step %s failed" % emr_step_id)

        raise EmrError("EMR step %s failed" % emr_step_id)

    def _check_for_missing_default_iam_roles(self, log, cluster):
        """If cluster couldn't start due to missing IAM roles, tell user what to do."""

        check.dict_param(cluster, "cluster")

        reason = _get_reason(cluster)
        if any(
            reason.endswith("/%s is invalid" % role)
            for role in (_FALLBACK_INSTANCE_PROFILE, _FALLBACK_SERVICE_ROLE)
        ):
            log.warning(
                "IAM roles are missing. See documentation for IAM roles on EMR here: "
                "https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-iam-roles.html"
            )

    def log_location_for_cluster(self, cluster_id):
        """EMR clusters are typically launched with S3 logging configured. This method inspects a
        cluster using boto3 describe_cluster to retrieve the log URI.

        Args:
            cluster_id (str): The cluster to inspect.

        Raises:
            EmrError: the log URI was missing (S3 log mirroring not enabled for this cluster)

        Returns:
            (str, str): log bucket and key
        """
        check.str_param(cluster_id, "cluster_id")

        # The S3 log URI is specified per job flow (cluster)
        log_uri = self.describe_cluster(cluster_id)["Cluster"].get("LogUri", None)

        # ugh, seriously boto3?! This will come back as string "None"
        if log_uri == "None" or log_uri is None:
            raise EmrError("Log URI not specified, cannot retrieve step execution logs")

        # For some reason the API returns an s3n:// protocol log URI instead of s3://
        log_uri = re.sub("^s3n", "s3", log_uri)
        log_uri_parsed = urlparse(log_uri)
        log_bucket = log_uri_parsed.netloc
        log_key_prefix = log_uri_parsed.path.lstrip("/")
        return log_bucket, log_key_prefix

    def retrieve_logs_for_step_id(self, log, cluster_id, step_id):
        """Retrieves stdout and stderr logs for the given step ID.

        Args:
            log (DagsterLogManager): Log manager, for logging
            cluster_id (str): EMR cluster ID
            step_id (str): EMR step ID for the job that was submitted.

        Returns
            (str, str): Tuple of stdout log string contents, and stderr log string contents
        """
        check.str_param(cluster_id, "cluster_id")
        check.str_param(step_id, "step_id")

        log_bucket, log_key_prefix = self.log_location_for_cluster(cluster_id)

        prefix = "{log_key_prefix}{cluster_id}/steps/{step_id}".format(
            log_key_prefix=log_key_prefix, cluster_id=cluster_id, step_id=step_id
        )
        stdout_log = self.wait_for_log(log, log_bucket, "{prefix}/stdout.gz".format(prefix=prefix))
        stderr_log = self.wait_for_log(log, log_bucket, "{prefix}/stderr.gz".format(prefix=prefix))
        return stdout_log, stderr_log

    def wait_for_log(self, log, log_bucket, log_key, waiter_delay=30, waiter_max_attempts=20):
        """Wait for gzipped EMR logs to appear on S3. Note that EMR syncs logs to S3 every 5
        minutes, so this may take a long time.

        Args:
            log_bucket (str): S3 bucket where log is expected to appear
            log_key (str): S3 key for the log file
            waiter_delay (int): How long to wait between attempts to check S3 for the log file
            waiter_max_attempts (int): Number of attempts before giving up on waiting

        Raises:
            EmrError: Raised if we waited the full duration and the logs did not appear

        Returns:
            str: contents of the log file
        """
        check.str_param(log_bucket, "log_bucket")
        check.str_param(log_key, "log_key")
        check.int_param(waiter_delay, "waiter_delay")
        check.int_param(waiter_max_attempts, "waiter_max_attempts")

        log.info(
            "Attempting to get log: s3://{log_bucket}/{log_key}".format(
                log_bucket=log_bucket, log_key=log_key
            )
        )

        s3 = _wrap_aws_client(boto3.client("s3"), min_backoff=self.check_cluster_every)
        waiter = s3.get_waiter("object_exists")
        try:
            waiter.wait(
                Bucket=log_bucket,
                Key=log_key,
                WaiterConfig={"Delay": waiter_delay, "MaxAttempts": waiter_max_attempts},
            )
        except WaiterError as err:
            raise EmrError("EMR log file did not appear on S3 after waiting") from err

        obj = BytesIO(s3.get_object(Bucket=log_bucket, Key=log_key)["Body"].read())
        gzip_file = gzip.GzipFile(fileobj=obj)
        return gzip_file.read().decode("utf-8")


def _get_reason(cluster_or_step):
    """Get state change reason message."""
    # StateChangeReason is {} before the first state change
    return cluster_or_step["Status"]["StateChangeReason"].get("Message", "")
