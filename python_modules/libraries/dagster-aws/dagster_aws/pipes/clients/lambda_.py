import json
from collections.abc import Mapping
from typing import Any, Optional, Union

import boto3
from dagster import PipesClient
from dagster._annotations import public
from dagster._core.definitions.resource_annotation import TreatAsResourceParam
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import (
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
)
from dagster._core.pipes.utils import open_pipes_session

from dagster_aws.pipes.context_injectors import PipesLambdaEventContextInjector
from dagster_aws.pipes.message_readers import PipesLambdaLogsMessageReader


class PipesLambdaClient(PipesClient, TreatAsResourceParam):
    """A pipes client for invoking AWS lambda.

    By default context is injected via the lambda input event and messages are parsed out of the
    4k tail of logs.

    Args:
        client (boto3.client): The boto lambda client used to call invoke.
        context_injector (Optional[PipesContextInjector]): A context injector to use to inject
            context into the lambda function. Defaults to :py:class:`PipesLambdaEventContextInjector`.
        message_reader (Optional[PipesMessageReader]): A message reader to use to read messages
            from the lambda function. Defaults to :py:class:`PipesLambdaLogsMessageReader`.
    """

    def __init__(
        self,
        client: Optional[boto3.client] = None,  # pyright: ignore (reportGeneralTypeIssues)
        context_injector: Optional[PipesContextInjector] = None,
        message_reader: Optional[PipesMessageReader] = None,
    ):
        self._client = client or boto3.client("lambda")
        self._message_reader = message_reader or PipesLambdaLogsMessageReader()
        self._context_injector = context_injector or PipesLambdaEventContextInjector()

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @public
    def run(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        *,
        function_name: str,
        event: Mapping[str, Any],
        context: Union[OpExecutionContext, AssetExecutionContext],
    ) -> PipesClientCompletedInvocation:
        """Synchronously invoke a lambda function, enriched with the pipes protocol.

        Args:
            function_name (str): The name of the function to use.
            event (Mapping[str, Any]): A JSON serializable object to pass as input to the lambda.
            context (Union[OpExecutionContext, AssetExecutionContext]): The context of the currently executing Dagster op or asset.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
            process.
        """
        with open_pipes_session(
            context=context,
            message_reader=self._message_reader,
            context_injector=self._context_injector,
        ) as session:
            other_kwargs = {}
            if isinstance(self._message_reader, PipesLambdaLogsMessageReader):
                other_kwargs["LogType"] = "Tail"

            if isinstance(self._context_injector, PipesLambdaEventContextInjector):
                payload_data = {
                    **event,
                    **session.get_bootstrap_env_vars(),
                }
            else:
                payload_data = event

            response = self._client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(payload_data),
                **other_kwargs,
            )
            if isinstance(self._message_reader, PipesLambdaLogsMessageReader):
                self._message_reader.consume_lambda_logs(response)

            if "FunctionError" in response:
                err_payload = json.loads(response["Payload"].read().decode("utf-8"))

                raise Exception(
                    f"Lambda Function Error ({response['FunctionError']}):\n{json.dumps(err_payload, indent=2)}"
                )

        # should probably have a way to return the lambda result payload
        return PipesClientCompletedInvocation(session)
