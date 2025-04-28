import time
from typing import TYPE_CHECKING, Any, Literal, Optional, Union, cast

import boto3
import dagster._check as check
from dagster import PipesClient
from dagster._annotations import preview, public
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
from dagster._core.pipes.context import PipesSession
from dagster._core.pipes.utils import PipesEnvContextInjector, open_pipes_session

from dagster_aws.pipes.clients.utils import WaiterConfig, emr_inject_pipes_env_vars
from dagster_aws.pipes.message_readers import PipesCloudWatchMessageReader

if TYPE_CHECKING:
    from mypy_boto3_emr_containers.client import EMRContainersClient
    from mypy_boto3_emr_containers.type_defs import (
        DescribeJobRunResponseTypeDef,
        StartJobRunRequestTypeDef,
        StartJobRunResponseTypeDef,
    )

AWS_SERVICE_NAME = "EMR Containers"


@public
@preview
class PipesEMRContainersClient(PipesClient, TreatAsResourceParam):
    """A pipes client for running workloads on AWS EMR Containers.

    Args:
        client (Optional[boto3.client]): The boto3 AWS EMR containers client used to interact with AWS EMR Containers.
        context_injector (Optional[PipesContextInjector]): A context injector to use to inject
            context into AWS EMR Containers workload. Defaults to :py:class:`PipesEnvContextInjector`.
        message_reader (Optional[PipesMessageReader]): A message reader to use to read messages
            from the AWS EMR Containers workload. It's recommended to use :py:class:`PipesS3MessageReader`.
        forward_termination (bool): Whether to cancel the AWS EMR Containers workload if the Dagster process receives a termination signal.
        pipes_params_bootstrap_method (Literal["args", "env"]): The method to use to inject parameters into the AWS EMR Containers workload. Defaults to "args".
        waiter_config (Optional[WaiterConfig]): Optional waiter configuration to use. Defaults to 70 days (Delay: 6, MaxAttempts: 1000000).
    """

    AWS_SERVICE_NAME = AWS_SERVICE_NAME

    def __init__(
        self,
        client: Optional["EMRContainersClient"] = None,
        context_injector: Optional[PipesContextInjector] = None,
        message_reader: Optional[PipesMessageReader] = None,
        forward_termination: bool = True,
        pipes_params_bootstrap_method: Literal["args", "env"] = "env",
        waiter_config: Optional[WaiterConfig] = None,
    ):
        self._client = client or boto3.client("emr-containers")
        self._context_injector = context_injector or PipesEnvContextInjector()
        self._message_reader = message_reader or PipesCloudWatchMessageReader()
        self.forward_termination = check.bool_param(forward_termination, "forward_termination")
        self.pipes_params_bootstrap_method = pipes_params_bootstrap_method
        self.waiter_config = waiter_config or WaiterConfig(Delay=6, MaxAttempts=1000000)

    @property
    def client(self) -> "EMRContainersClient":
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
        start_job_run_params: "StartJobRunRequestTypeDef",
        extras: Optional[dict[str, Any]] = None,
    ) -> PipesClientCompletedInvocation:
        """Run a workload on AWS EMR Containers, enriched with the pipes protocol.

        Args:
            context (Union[OpExecutionContext, AssetExecutionContext]): The context of the currently executing Dagster op or asset.
            params (dict): Parameters for the ``start_job_run`` boto3 AWS EMR Containers client call.
                See `Boto3 EMR Containers API Documentation <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/emr-containers/client/start_job_run.html>`_
            extras (Optional[Dict[str, Any]]): Additional information to pass to the Pipes session in the external process.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
            process.
        """
        with open_pipes_session(
            context=context,
            message_reader=self.message_reader,
            context_injector=self.context_injector,
            extras=extras,
        ) as session:
            start_job_run_params = self._enrich_start_params(context, session, start_job_run_params)
            start_response = self._start(context, start_job_run_params)
            try:
                completion_response = self._wait_for_completion(context, start_response)
                context.log.info(f"[pipes] {self.AWS_SERVICE_NAME} workload is complete!")
                return PipesClientCompletedInvocation(
                    session, metadata=self._extract_dagster_metadata(completion_response)
                )

            except DagsterExecutionInterruptedError:
                if self.forward_termination:
                    context.log.warning(
                        f"[pipes] Dagster process interrupted! Will terminate external {self.AWS_SERVICE_NAME} workload."
                    )
                    self._terminate(context, start_response)
                raise

    def _enrich_start_params(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        session: PipesSession,
        params: "StartJobRunRequestTypeDef",
    ) -> "StartJobRunRequestTypeDef":
        # inject Dagster tags
        tags = params.get("tags", {})
        params["tags"] = {**tags, **session.default_remote_invocation_info}

        params["jobDriver"] = params.get("jobDriver", {})

        if self.pipes_params_bootstrap_method == "env":
            params["configurationOverrides"] = params.get("configurationOverrides", {})
            params["configurationOverrides"]["applicationConfiguration"] = params[  # type: ignore
                "configurationOverrides"
            ].get("applicationConfiguration", [])
            # we can reuse the same method as in standard EMR
            # since configurations format is the same
            params["configurationOverrides"]["applicationConfiguration"] = (  # type: ignore
                emr_inject_pipes_env_vars(
                    session,
                    params["configurationOverrides"]["applicationConfiguration"],  # type: ignore
                    emr_flavor="containers",
                )
            )

        # the other option is sparkSqlJobDriver - in this case there won't be a remote Pipes session
        # and no Pipes messages will arrive from the job
        # but we can still run it and get the logs
        if spark_submit_job_driver := params["jobDriver"].get("sparkSubmitJobDriver"):
            if self.pipes_params_bootstrap_method == "args":
                spark_submit_job_driver["sparkSubmitParameters"] = spark_submit_job_driver.get(
                    "sparkSubmitParameters", ""
                )

                for key, value in session.get_bootstrap_cli_arguments().items():
                    spark_submit_job_driver["sparkSubmitParameters"] += f" {key} {value}"

            params["jobDriver"]["sparkSubmitJobDriver"] = spark_submit_job_driver  # type: ignore

        return cast("StartJobRunRequestTypeDef", params)

    def _start(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        params: "StartJobRunRequestTypeDef",
    ) -> "StartJobRunResponseTypeDef":
        response = self.client.start_job_run(**params)

        virtual_cluster_id = response["virtualClusterId"]
        job_run_id = response["id"]

        context.log.info(
            f"[pipes] {self.AWS_SERVICE_NAME} job started with job_run_id {job_run_id} on virtual cluster {virtual_cluster_id}."
        )

        return response

    def _wait_for_completion(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        start_response: "StartJobRunResponseTypeDef",
    ) -> "DescribeJobRunResponseTypeDef":
        job_run_id = start_response["id"]
        virtual_cluster_id = start_response["virtualClusterId"]

        # TODO: use a native boto3 waiter instead of a while loop
        # once it's available (it does not exist at the time of writing)
        attempts = 0
        while attempts < self.waiter_config.get("MaxAttempts", 1000000):
            response = self.client.describe_job_run(
                id=job_run_id, virtualClusterId=virtual_cluster_id
            )
            state = response["jobRun"].get("state")

            if state in ["COMPLETED", "FAILED", "CANCELLED"]:
                break

            time.sleep(self.waiter_config.get("Delay", 6))

        if state in ["FAILED", "CANCELLED"]:  # pyright: ignore[reportPossiblyUnboundVariable]
            raise RuntimeError(
                f"EMR Containers job run {job_run_id} failed with state {state}. Reason: {response['jobRun'].get('failureReason')}, details: {response['jobRun'].get('stateDetails')}"  # pyright: ignore[reportPossiblyUnboundVariable]
            )

        return self.client.describe_job_run(virtualClusterId=virtual_cluster_id, id=job_run_id)

    def _extract_dagster_metadata(
        self, response: "DescribeJobRunResponseTypeDef"
    ) -> RawMetadataMapping:
        metadata: RawMetadataMapping = {}

        metadata["AWS EMR Containers Virtual Cluster ID"] = response["jobRun"].get(
            "virtualClusterId"
        )
        metadata["AWS EMR Containers Job Run ID"] = response["jobRun"].get("id")

        # TODO: it would be great to add a url to EMR Studio page for this run
        # such urls look like: https://es-638xhdetxum2td9nc3a45evmn.emrstudio-prod.eu-north-1.amazonaws.com/#/containers-applications/00fm4oe0607u5a1d
        # but we need to get the Studio ID from the application_id
        # which is not possible with the current AWS API

        return metadata

    def _terminate(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        start_response: "StartJobRunResponseTypeDef",
    ):
        virtual_cluster_id = start_response["virtualClusterId"]
        job_run_id = start_response["id"]
        context.log.info(f"[pipes] Terminating {self.AWS_SERVICE_NAME} job run {job_run_id}")
        self.client.cancel_job_run(virtualClusterId=virtual_cluster_id, id=job_run_id)
        context.log.info(f"[pipes] {self.AWS_SERVICE_NAME} job run {job_run_id} terminated.")
