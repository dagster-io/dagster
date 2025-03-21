import os
import sys
import time
from typing import TYPE_CHECKING, Any, Optional, Union, cast

import boto3
import dagster._check as check
from dagster import MetadataValue, PipesClient
from dagster._annotations import public
from dagster._core.definitions.metadata import RawMetadataMapping
from dagster._core.definitions.resource_annotation import TreatAsResourceParam
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import (
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
)
from dagster._core.pipes.utils import PipesEnvContextInjector, PipesSession, open_pipes_session

from dagster_aws.emr.emr import EMR_CLUSTER_TERMINATED_STATES
from dagster_aws.pipes.clients.utils import emr_inject_pipes_env_vars
from dagster_aws.pipes.message_readers import (
    PipesS3LogReader,
    PipesS3MessageReader,
    gzip_log_decode_fn,
)

if TYPE_CHECKING:
    from mypy_boto3_emr import EMRClient
    from mypy_boto3_emr.literals import ClusterStateType
    from mypy_boto3_emr.type_defs import (
        ConfigurationTypeDef,
        DescribeClusterOutputTypeDef,
        RunJobFlowInputTypeDef,
        RunJobFlowOutputTypeDef,
    )


@public
class PipesEMRClient(PipesClient, TreatAsResourceParam):
    """A pipes client for running jobs on AWS EMR.

    Args:
        message_reader (Optional[PipesMessageReader]): A message reader to use to read messages
            from the EMR jobs. Recommended to use :py:class:`PipesS3MessageReader` with `expect_s3_message_writer` set to `True`.
        client (Optional[boto3.client]): The boto3 EMR client used to interact with AWS EMR.
        context_injector (Optional[PipesContextInjector]): A context injector to use to inject
            context into AWS EMR job. Defaults to :py:class:`PipesEnvContextInjector`.
        forward_termination (bool): Whether to cancel the EMR job if the Dagster process receives a termination signal.
        wait_for_s3_logs_seconds (int): The number of seconds to wait for S3 logs to be written after execution completes.
        s3_application_logs_prefix (str): The prefix to use when looking for application logs in S3.
            Defaults to `containers`. Another common value is `steps` (for non-yarn clusters).
    """

    def __init__(
        self,
        message_reader: PipesMessageReader,
        client: Optional["EMRClient"] = None,
        context_injector: Optional[PipesContextInjector] = None,
        forward_termination: bool = True,
        wait_for_s3_logs_seconds: int = 10,
        s3_application_logs_prefix: str = "containers",
    ):
        self._client: EMRClient = cast("EMRClient", client or boto3.client("emr"))
        self._message_reader = message_reader
        self._context_injector = context_injector or PipesEnvContextInjector()
        self.forward_termination = check.bool_param(forward_termination, "forward_termination")
        self.wait_for_s3_logs_seconds = wait_for_s3_logs_seconds
        self.s3_application_logs_prefix = s3_application_logs_prefix

    @property
    def client(self) -> "EMRClient":
        return self._client

    @property
    def context_injector(self) -> PipesContextInjector:
        return self._context_injector

    @property
    def message_reader(self) -> PipesMessageReader:
        return self._message_reader

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @public
    def run(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        *,
        context: Union[OpExecutionContext, AssetExecutionContext],
        run_job_flow_params: "RunJobFlowInputTypeDef",
        extras: Optional[dict[str, Any]] = None,
    ) -> PipesClientCompletedInvocation:
        """Run a job on AWS EMR, enriched with the pipes protocol.

        Starts a new EMR cluster for each invocation.

        Args:
            context (Union[OpExecutionContext, AssetExecutionContext]): The context of the currently executing Dagster op or asset.
            run_job_flow_params (Optional[dict]): Parameters for the ``run_job_flow`` boto3 EMR client call.
                See `Boto3 EMR API Documentation <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/emr/client/emr.html#emr>`_
            extras (Optional[Dict[str, Any]]): Additional information to pass to the Pipes session in the external process.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external process.
        """
        with open_pipes_session(
            context=context,
            message_reader=self.message_reader,
            context_injector=self.context_injector,
            extras=extras,
        ) as session:
            run_job_flow_params = self._enrich_params(session, run_job_flow_params)
            start_response = self._start(context, session, run_job_flow_params)
            try:
                self._add_log_readers(context, start_response)
                wait_response = self._wait_for_completion(context, start_response)
                self._read_application_logs(context, session, wait_response)
                return PipesClientCompletedInvocation(
                    session, metadata=self._extract_dagster_metadata(wait_response)
                )

            except DagsterExecutionInterruptedError:
                if self.forward_termination:
                    context.log.warning(
                        "[pipes] Dagster process interrupted! Will terminate external EMR job."
                    )
                    self._terminate(context, start_response)
                raise

    def _enrich_params(
        self, session: PipesSession, params: "RunJobFlowInputTypeDef"
    ) -> "RunJobFlowInputTypeDef":
        params["Configurations"] = emr_inject_pipes_env_vars(
            session,
            cast(list["ConfigurationTypeDef"], params.get("Configurations", [])),
            emr_flavor="standard",
        )

        tags = list(params.get("Tags", []))

        for key, value in session.default_remote_invocation_info.items():
            tags.append({"Key": key, "Value": value})

        params["Tags"] = tags

        return params

    def _start(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        session: PipesSession,
        params: "RunJobFlowInputTypeDef",
    ) -> "RunJobFlowOutputTypeDef":
        response = self._client.run_job_flow(**params)

        session.report_launched({"extras": response})

        cluster_id = response["JobFlowId"]

        context.log.info(f"[pipes] EMR steps started in cluster {cluster_id}")
        return response

    def _wait_for_completion(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        response: "RunJobFlowOutputTypeDef",
    ) -> "DescribeClusterOutputTypeDef":
        cluster_id = response["JobFlowId"]
        self._client.get_waiter("cluster_running").wait(ClusterId=cluster_id)
        context.log.info(f"[pipes] EMR cluster {cluster_id} running")
        # now wait for the job to complete
        self._client.get_waiter("cluster_terminated").wait(ClusterId=cluster_id)

        cluster = self._client.describe_cluster(ClusterId=cluster_id)

        state: ClusterStateType = cluster["Cluster"]["Status"]["State"]  # type: ignore

        context.log.info(f"[pipes] EMR cluster {cluster_id} completed with state: {state}")

        if state in EMR_CLUSTER_TERMINATED_STATES:
            context.log.error(f"[pipes] EMR job {cluster_id} failed")
            raise Exception(f"[pipes] EMR job {cluster_id} failed:\n{cluster}")

        return cluster

    def _add_log_readers(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        response: "RunJobFlowOutputTypeDef",
    ):
        cluster = self.client.describe_cluster(ClusterId=response["JobFlowId"])

        cluster_id = cluster["Cluster"]["Id"]  # type: ignore
        logs_uri = cluster.get("Cluster", {}).get("LogUri", {})

        if isinstance(self.message_reader, PipesS3MessageReader) and logs_uri is None:
            context.log.warning(
                "[pipes] LogUri is not set in the EMR cluster configuration. Won't be able to read logs."
            )
        elif isinstance(self.message_reader, PipesS3MessageReader) and isinstance(logs_uri, str):
            bucket = logs_uri.split("/")[2]
            prefix = "/".join(logs_uri.split("/")[3:])

            steps = self.client.list_steps(ClusterId=cluster_id)

            # forward stdout and stderr from each step

            for step in steps["Steps"]:
                step_id = step["Id"]  # type: ignore

                for stdio in ["stdout", "stderr"]:
                    # at this stage we can't know if this key will be created
                    # for example, if a step doesn't have any stdout/stderr logs
                    # the PipesS3LogReader won't be able to start
                    # this may result in some unnecessary warnings
                    # there is not much we can do about it except perform step logs reading
                    # after the job is completed, which is not ideal too
                    key = os.path.join(prefix, f"{cluster_id}/steps/{step_id}/{stdio}.gz")

                    self.message_reader.add_log_reader(
                        log_reader=PipesS3LogReader(
                            client=self.message_reader.client,
                            bucket=bucket,
                            key=key,
                            decode_fn=gzip_log_decode_fn,
                            target_stream=sys.stdout if stdio == "stdout" else sys.stderr,
                            debug_info=f"reader for {stdio} of EMR step {step_id}",
                        ),
                    )

    def _read_application_logs(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        session: PipesSession,
        response: "DescribeClusterOutputTypeDef",
    ):
        if (
            isinstance(self.message_reader, PipesS3MessageReader)
            and self.message_reader.include_stdio_in_messages
        ):
            # driver logs already have been consumed from Pipes messages
            # no need to read any files from S3
            return

        cluster_id = response["Cluster"]["Id"]  # type: ignore
        logs_uri = response.get("Cluster", {}).get("LogUri", {})

        if isinstance(self.message_reader, PipesS3MessageReader) and isinstance(logs_uri, str):
            bucket = logs_uri.split("/")[2]
            prefix = "/".join(logs_uri.split("/")[3:])

            # discover application logs (e.g. Python logs) and forward all of them
            # ex. /containers/application_1727881613116_0001/container_1727881613116_0001_01_000001/stdout.gz for Yarn
            # or /steps/... for EMR steps
            application_logs_prefix = os.path.join(
                prefix, f"{cluster_id}/{self.s3_application_logs_prefix}/"
            )

            context.log.debug(
                f"[pipes] Waiting for {self.wait_for_s3_logs_seconds} seconds to allow EMR to dump all logs to S3. "
                "Consider increasing this value if some logs are missing."
            )

            time.sleep(self.wait_for_s3_logs_seconds)  # give EMR a chance to dump all logs to S3

            context.log.debug(
                f"[pipes] Looking for application logs in s3://{os.path.join(bucket, application_logs_prefix)}"
            )

            all_keys = [
                obj["Key"]
                for obj in self.message_reader.client.list_objects_v2(
                    Bucket=bucket, Prefix=application_logs_prefix
                )["Contents"]
            ]

            # filter keys which include stdout.gz or stderr.gz

            container_log_keys = {}
            for key in all_keys:
                if "stdout.gz" in key:
                    container_log_keys[key] = "stdout"
                elif "stderr.gz" in key:
                    container_log_keys[key] = "stderr"

            # forward application logs

            for key, stdio in container_log_keys.items():
                container_id = key.split("/")[-2]
                self.message_reader.add_log_reader(
                    log_reader=PipesS3LogReader(
                        client=self.message_reader.client,
                        bucket=bucket,
                        key=key,
                        decode_fn=gzip_log_decode_fn,
                        target_stream=sys.stdout if stdio == "stdout" else sys.stderr,
                        debug_info=f"log reader for container {container_id} {stdio}",
                    ),
                )

    def _extract_dagster_metadata(
        self, response: "DescribeClusterOutputTypeDef"
    ) -> RawMetadataMapping:
        metadata: RawMetadataMapping = {}

        region = self.client.meta.region_name

        cluster = response["Cluster"]

        if cluster_id := cluster.get("Id"):
            metadata["AWS EMR Cluster ID"] = cluster_id

        if log_uri := cluster.get("LogUri"):
            # LogUri originally points to a shared S3 bucket where logs from all clusters are stored
            # which is not very useful
            metadata["AWS EMR Log URI"] = MetadataValue.path(log_uri + f"{cluster_id}")

        if cluster_id:
            metadata["AWS EMR Cluster"] = MetadataValue.url(
                f"https://{region}.console.aws.amazon.com/emr/home?region={region}#/clusterDetails/{cluster_id}"
            )

        return metadata

    def _terminate(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        start_response: "RunJobFlowOutputTypeDef",
    ):
        cluster_id = start_response["JobFlowId"]
        context.log.info(f"[pipes] Terminating EMR job {cluster_id}")
        self._client.terminate_job_flows(JobFlowIds=[cluster_id])
