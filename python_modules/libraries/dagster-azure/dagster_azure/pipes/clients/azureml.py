import time
from typing import Optional, Union

import dagster._check as check
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Command
from dagster._core.definitions.resource_annotation import TreatAsResourceParam
from dagster._core.errors import DagsterExecutionInterruptedError, DagsterPipesExecutionError
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from dagster._core.pipes.client import (
    PipesClient,
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
)
from dagster._core.pipes.utils import open_pipes_session
from dagster_pipes import PipesExtras


class PipesAzureMLClient(PipesClient, TreatAsResourceParam):
    """Pipes client for Azure ML.

    Args:
        client (MLClient): An Azure ML `MLClient` object.
        context_injector (PipesContextInjector): A context injector to use to inject
            context into the Azure ML job process.
        message_reader (PipesMessageReader): A message reader to use to read messages
            from the Azure ML job.
        poll_interval_seconds (float): How long to sleep between checking the status of the job run.
            Defaults to 5.
        forward_termination (bool): Whether to cancel the Azure ML job if the orchestration process
            is interrupted or canceled. Defaults to True.
    """

    def __init__(
        self,
        client: MLClient,
        context_injector: PipesContextInjector,
        message_reader: PipesMessageReader,
        poll_interval_seconds: float = 5,
        forward_termination: bool = True,
    ):
        self.client = client
        self.context_injector = check.inst_param(
            context_injector,
            "context_injector",
            PipesContextInjector,
        )
        self.message_reader = check.inst_param(
            message_reader,
            "message_reader",
            PipesMessageReader,
        )
        self.poll_interval_seconds = check.numeric_param(
            poll_interval_seconds, "poll_interval_seconds"
        )
        self.forward_termination = check.bool_param(forward_termination, "forward_termination")

    def _poll_til_success(
        self, context: Union[OpExecutionContext, AssetExecutionContext], job_name: str
    ) -> None:
        # poll the Azure ML job until it completes successfully, raising otherwise

        last_observed_status = None

        while True:
            status = self.client.jobs.get(job_name).status

            if status != last_observed_status:
                context.log.info(
                    f"[pipes] Azure ML job {job_name} observed state transition to {status}"
                )
            last_observed_status = status

            if status == "Completed":
                return
            elif status in {"Canceled", "Failed"}:
                raise DagsterPipesExecutionError(f"Error running Azure ML job: {status}")

            time.sleep(self.poll_interval_seconds)

    def _poll_til_terminating(self, job_name: str) -> None:
        while True:
            status = self.client.jobs.get(job_name).status
            if status in {"Completed", "Canceled", "Failed"}:
                return

            time.sleep(self.poll_interval_seconds)

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def run(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        *,
        context: Union[OpExecutionContext, AssetExecutionContext],
        extras: Optional[PipesExtras] = None,
        command: Command,
    ) -> PipesClientCompletedInvocation:
        """Synchronously execute an Azure ML job with the pipes protocol.

        Args:
            command (azure.ai.ml.entities.Command): Specification of the Azure ML
                command job to run. Pipes bootstrap parameters will be passed via environment
                variables which will be merged with any existing environment variables in the command.
                The Azure ML job code should use :py:func:`dagster_pipes.open_dagster_pipes` to
                initialize the Pipes connection.
            context (Union[OpExecutionContext, AssetExecutionContext]): The context from the executing op or asset.
            extras (Optional[PipesExtras]): An optional dict of extra parameters to pass to the
                Azure ML job.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
                process.
        """
        with open_pipes_session(
            context=context,
            extras=extras,
            context_injector=self.context_injector,
            message_reader=self.message_reader,
        ) as pipes_session:
            command.environment_variables = {
                **command.environment_variables,
                **pipes_session.get_bootstrap_env_vars(),
            }
            job = self.client.create_or_update(command)

            try:
                self._poll_til_success(context, job.name)  # pyright: ignore[reportArgumentType]
            except DagsterExecutionInterruptedError:
                if self.forward_termination:
                    context.log.info("[pipes] execution interrupted, canceling Azure ML job.")
                    self.client.jobs.begin_cancel(job.name)  # pyright: ignore[reportArgumentType]
                    self._poll_til_terminating(job.name)  # pyright: ignore[reportArgumentType]

        return PipesClientCompletedInvocation(
            pipes_session, metadata={"AzureML Job Name": job.name}
        )
