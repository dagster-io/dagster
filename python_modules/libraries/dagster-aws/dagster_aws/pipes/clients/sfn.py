import time
from typing import TYPE_CHECKING, Any, Optional, Union, cast

import boto3
import dagster._check as check
from botocore.exceptions import ClientError
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
from dagster._core.pipes.utils import PipesEnvContextInjector, open_pipes_session

from dagster_aws.pipes.message_readers import PipesCloudWatchMessageReader

if TYPE_CHECKING:
    from mypy_boto3_stepfunctions import SFNClient
    from mypy_boto3_stepfunctions.type_defs import (
        DescribeExecutionOutputTypeDef,
        StartExecutionInputRequestTypeDef,
    )


@experimental
class PipesSFNClient(PipesClient, TreatAsResourceParam):
    """A pipes client for invoking AWS Step Functions.

    Args:
        context_injector (Optional[PipesContextInjector]): A context injector to use to inject
            context into the Step Function execution.
        message_reader (Optional[PipesMessageReader]): A message reader to use to read messages
            from the Step Function execution. Defaults to :py:class:`PipesCloudWatchMessageReader`.
        client (Optional[boto3.client]): The boto Step Functions client used to start the execution.
        forward_termination (bool): Whether to cancel the Step Function execution when the Dagster process receives a termination signal.
    """

    def __init__(
        self,
        context_injector: Optional[PipesContextInjector] = None,
        message_reader: Optional[PipesMessageReader] = None,
        client: Optional["SFNClient"] = None,
        forward_termination: bool = True,
    ):
        self._client: SFNClient = client or boto3.client("stepfunctions")
        self._context_injector = context_injector or PipesEnvContextInjector()
        self._message_reader = message_reader or PipesCloudWatchMessageReader()
        self.forward_termination = check.bool_param(forward_termination, "forward_termination")

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @public
    def run(
        self,
        *,
        context: Union[OpExecutionContext, AssetExecutionContext],
        start_execution_input: "StartExecutionInputRequestTypeDef",
        extras: Optional[dict[str, Any]] = None,
    ) -> PipesClientCompletedInvocation:
        """Start a Step Function execution, enriched with the pipes protocol.

        See also: `AWS API Documentation <https://docs.aws.amazon.com/step-functions/latest/apireference/API_StartExecution.html>`_

        Args:
            context (Union[OpExecutionContext, AssetExecutionContext]): The context of the currently executing Dagster op or asset.
            start_execution_input (Dict): Parameters for the ``start_execution`` boto3 Step Functions client call.
            extras (Optional[Dict[str, Any]]): Additional Dagster metadata to pass to the Step Function execution.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
            process.
        """
        params = start_execution_input

        state_machine_arn = cast(str, params["stateMachineArn"])

        with open_pipes_session(
            context=context,
            message_reader=self._message_reader,
            context_injector=self._context_injector,
            extras=extras,
        ) as session:
            try:
                execution_arn = self._client.start_execution(**params)["executionArn"]

            except ClientError as err:
                error_info = err.response.get("Error", {})
                context.log.error(
                    "Couldn't start execution %s. Here's why: %s: %s",
                    state_machine_arn,
                    error_info.get("Code", "Unknown error"),
                    error_info.get("Message", "No error message available"),
                )
                raise

            response = self._client.describe_execution(executionArn=execution_arn)
            context.log.info(
                f"Started AWS Step Function execution {state_machine_arn} run: {execution_arn}"
            )

            try:
                response = self._wait_for_execution_completion(execution_arn)
            except DagsterExecutionInterruptedError:
                if self.forward_termination:
                    self._terminate_execution(context=context, execution_arn=execution_arn)
                raise

            status = response["status"]
            if status != "SUCCEEDED":
                raise RuntimeError(
                    f"Step Function execution {state_machine_arn} run {execution_arn} completed with status {status} :\n{response.get('errorMessage')}"
                )
            else:
                context.log.info(
                    f"Step Function execution {state_machine_arn} run {execution_arn} completed successfully"
                )

        return PipesClientCompletedInvocation(
            session, metadata=self._extract_dagster_metadata(response)
        )

    def _wait_for_execution_completion(
        self, execution_arn: str
    ) -> "DescribeExecutionOutputTypeDef":
        while True:
            response = self._client.describe_execution(executionArn=execution_arn)
            if response["status"] in ["FAILED", "SUCCEEDED", "TIMED_OUT", "ABORTED"]:
                return response
            time.sleep(5)

    def _extract_dagster_metadata(
        self, response: "DescribeExecutionOutputTypeDef"
    ) -> RawMetadataMapping:
        metadata: RawMetadataMapping = {}
        metadata["executionArn"] = MetadataValue.text(response["executionArn"])
        return metadata

    def _terminate_execution(
        self, context: Union[OpExecutionContext, AssetExecutionContext], execution_arn: str
    ):
        """Creates a handler which will gracefully stop the Run in case of external termination.
        It will stop the Step Function execution before doing so.
        """
        context.log.warning(
            f"[pipes] execution interrupted, stopping Step Function execution {execution_arn}..."
        )
        self._client.stop_execution(executionArn=execution_arn)
        context.log.warning(f"Successfully stopped Step Function execution {execution_arn}.")
