import abc
from typing import Any, Dict, Generic, Mapping, Optional, TypeVar

import dagster._check as check
from dagster import PipesClient
from dagster._annotations import public
from dagster._core.definitions.resource_annotation import TreatAsResourceParam
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import (
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
)
from dagster._core.pipes.utils import PipesEnvContextInjector, open_pipes_session

from dagster_aws.pipes.message_readers import PipesCloudWatchMessageReader

P_BOTO3_START_RUN = TypeVar("P_BOTO3_START_RUN", bound=Mapping[str, Any])
R_BOTO3_START_RUN = TypeVar("R_BOTO3_START_RUN", bound=Mapping[str, Any])
R_BOTO3_DESCRIBE_RUN = TypeVar("R_BOTO3_DESCRIBE_RUN", bound=Mapping[str, Any])


class PipesBaseClient(
    Generic[P_BOTO3_START_RUN, R_BOTO3_START_RUN, R_BOTO3_DESCRIBE_RUN],
    PipesClient,
    TreatAsResourceParam,
    abc.ABC,
):
    AWS_SERVICE_NAME = "CHANGE_ME"

    def __init__(
        self,
        client,
        context_injector: Optional[PipesContextInjector] = None,
        message_reader: Optional[PipesMessageReader] = None,
        forward_termination: bool = True,
    ):
        self._client = client
        self._context_injector = context_injector or PipesEnvContextInjector()
        self._message_reader = message_reader or PipesCloudWatchMessageReader()
        self.forward_termination = check.bool_param(forward_termination, "forward_termination")

    @property
    def client(self):
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

    def run(
        self,
        *,
        context: OpExecutionContext,
        params: P_BOTO3_START_RUN,
        extras: Optional[Dict[str, Any]] = None,
    ) -> PipesClientCompletedInvocation:
        with open_pipes_session(
            context=context,
            message_reader=self.message_reader,
            context_injector=self.context_injector,
            extras=extras,
        ) as session:
            start_response = self._start(context, params)
            try:
                completion_response = self._wait_for_completion(context, start_response)
                context.log.info(f"[pipes] {self.AWS_SERVICE_NAME} workload is complete!")
                self._read_messages(context, completion_response)
                return PipesClientCompletedInvocation(session)

            except DagsterExecutionInterruptedError:
                if self.forward_termination:
                    context.log.warning(
                        f"[pipes] Dagster process interrupted! Will terminate external {self.AWS_SERVICE_NAME} workload."
                    )
                    self._terminate(context, start_response)
                raise

    @abc.abstractmethod
    def _start(self, context: OpExecutionContext, params: P_BOTO3_START_RUN) -> R_BOTO3_START_RUN:
        pass

    @abc.abstractmethod
    def _wait_for_completion(
        self, context: OpExecutionContext, start_response: R_BOTO3_START_RUN
    ) -> R_BOTO3_DESCRIBE_RUN:
        pass

    @abc.abstractmethod
    def _terminate(self, context: OpExecutionContext, start_response: R_BOTO3_START_RUN) -> None:
        pass

    @abc.abstractmethod
    def _read_messages(
        self, context: OpExecutionContext, completion_response: R_BOTO3_DESCRIBE_RUN
    ) -> None:
        pass


def class_docstring(aws_service_name: str):
    def inner(obj):
        obj.__doc__ = f"""A pipes client for running workloads on AWS {aws_service_name}.

        Args:
            client (Optional[boto3.client]): The boto3 {aws_service_name} client used to interact with AWS {aws_service_name}.
            context_injector (Optional[PipesContextInjector]): A context injector to use to inject
                context into AWS {aws_service_name} workload. Defaults to :py:class:`PipesEnvContextInjector`.
            message_reader (Optional[PipesMessageReader]): A message reader to use to read messages
                from the {aws_service_name} workload. Defaults to :py:class:`PipesCloudWatchMessageReader`.
            forward_termination (bool): Whether to cancel the {aws_service_name} workload if the Dagster process receives a termination signal.
        """

        return obj

    return inner


def run_docstring(aws_service_name: str, boto3_method: str):
    service_lower_case = aws_service_name.lower()
    service_kebab_case = service_lower_case.replace("_", "-")

    def inner(obj):
        obj.__doc__ = f"""Run a workload on AWS {aws_service_name}, enriched with the pipes protocol.

            Args:
                context (OpExecutionContext): The context of the currently executing Dagster op or asset.
                params (dict): Parameters for the ``{boto3_method}`` boto3 {aws_service_name} client call.
                    See `Boto3 API Documentation <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/{service_lower_case}/client/{service_lower_case}.html#{service_kebab_case}>`_
                extras (Optional[Dict[str, Any]]): Additional information to pass to the Pipes session in the external process.

            Returns:
                PipesClientCompletedInvocation: Wrapper containing results reported by the external
                process.
            """
        return public(obj)

    return inner
