import os
import sys
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

import boto3
import dagster._check as check
from dagster import MetadataValue, PipesClient
from dagster._annotations import experimental, public
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
from dagster_aws.pipes.message_readers import (
    PipesS3LogReader,
    PipesS3MessageReader,
    gzip_log_decode_fn,
)

if TYPE_CHECKING:
    from mypy_boto3_emr import EMRClient
    from mypy_boto3_emr.literals import ClusterStateType
    from mypy_boto3_emr.type_defs import (
        ConfigurationUnionTypeDef,
        DescribeClusterOutputTypeDef,
        RunJobFlowInputRequestTypeDef,
        RunJobFlowOutputTypeDef,
    )


def add_configuration(
    configurations: list["ConfigurationUnionTypeDef"],
    configuration: "ConfigurationUnionTypeDef",
):
    """Add a configuration to a list of EMR configurations, merging configurations with the same classification.

    This is necessary because EMR doesn't accept multiple configurations with the same classification.
    """
    for existing_configuration in configurations:
        if existing_configuration.get("Classification") is not None and existing_configuration.get(
            "Classification"
        ) == configuration.get("Classification"):
            properties = {**existing_configuration.get("Properties", {})}
            properties.update(properties)

            inner_configurations = cast(
                list["ConfigurationUnionTypeDef"], existing_configuration.get("Configurations", [])
            )

            for inner_configuration in cast(
                list["ConfigurationUnionTypeDef"], configuration.get("Configurations", [])
            ):
                add_configuration(inner_configurations, inner_configuration)

            existing_configuration["Properties"] = properties
            existing_configuration["Configurations"] = inner_configurations  # type: ignore

            break
    else:
        configurations.append(configuration)


@public
@experimental
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
    """

    def __init__(
        self,
        message_reader: PipesMessageReader,
        client=None,
        context_injector: Optional[PipesContextInjector] = None,
        forward_termination: bool = True,
        wait_for_s3_logs_seconds: int = 10,
    ):
        self._client = client or boto3.client("emr")
        self._message_reader = message_reader
        self._context_injector = context_injector or PipesEnvContextInjector()
        self.forward_termination = check.bool_param(forward_termination, "forward_termination")
        self.wait_for_s3_logs_seconds = wait_for_s3_logs_seconds

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
    def run(
        self,
        *,
        context: Union[OpExecutionContext, AssetExecutionContext],
        run_job_flow_params: "RunJobFlowInputRequestTypeDef",
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
                self._read_remaining_logs(context, wait_response)
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
        self, session: PipesSession, params: "RunJobFlowInputRequestTypeDef"
    ) -> "RunJobFlowInputRequestTypeDef":
        # add Pipes env variables
        pipes_env_vars = session.get_bootstrap_env_vars()

        configurations = cast(list["ConfigurationUnionTypeDef"], params.get("Configurations", []))

        # add all possible env vars to spark-defaults, spark-env, yarn-env, hadoop-env
        # since we can't be sure which one will be used by the job
        add_configuration(
            configurations,
            {
                "Classification": "spark-defaults",
                "Properties": {
                    f"spark.yarn.appMasterEnv.{var}": value for var, value in pipes_env_vars.items()
                },
            },
        )

        for classification in ["spark-env", "yarn-env", "hadoop-env"]:
            add_configuration(
                configurations,
                {
                    "Classification": classification,
                    "Configurations": [
                        {
                            "Classification": "export",
                            "Properties": pipes_env_vars,
                        }
                    ],
                },
            )

        params["Configurations"] = configurations

        tags = list(params.get("Tags", []))

        for key, value in session.default_remote_invocation_info.items():
            tags.append({"Key": key, "Value": value})

        params["Tags"] = tags

        return params

    def _start(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        session: PipesSession,
        params: "RunJobFlowInputRequestTypeDef",
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

        state: ClusterStateType = cluster["Cluster"]["Status"]["State"]

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

    def _read_remaining_logs(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        response: "DescribeClusterOutputTypeDef",
    ):
        cluster_id = response["Cluster"]["Id"]  # type: ignore
        logs_uri = response.get("Cluster", {}).get("LogUri", {})

        if isinstance(self.message_reader, PipesS3MessageReader) and isinstance(logs_uri, str):
            bucket = logs_uri.split("/")[2]
            prefix = "/".join(logs_uri.split("/")[3:])

            # discover container (application) logs (e.g. Python logs) and forward all of them
            # ex. /containers/application_1727881613116_0001/container_1727881613116_0001_01_000001/stdout.gz
            containers_prefix = os.path.join(prefix, f"{cluster_id}/containers/")

            context.log.debug(
                f"[pipes] Waiting for {self.wait_for_s3_logs_seconds} seconds to allow EMR to dump all logs to S3. "
                "Consider increasing this value if some logs are missing."
            )

            time.sleep(self.wait_for_s3_logs_seconds)  # give EMR a chance to dump all logs to S3

            context.log.debug(
                f"[pipes] Looking for application logs in s3://{os.path.join(bucket, containers_prefix)}"
            )

            all_keys = [
                obj["Key"]
                for obj in self.message_reader.client.list_objects_v2(
                    Bucket=bucket, Prefix=containers_prefix
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
            metadata["AWS EMR Log URI"] = MetadataValue.path(log_uri)

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
