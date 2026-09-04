import time
from abc import abstractmethod
from typing import Literal
from uuid import UUID

import dagster._check as check
from dagster import PipesClient
from dagster._core.definitions.metadata import RawMetadataMapping, UrlMetadataValue
from dagster._core.definitions.resource_annotation import TreatAsResourceParam
from dagster._core.errors import DagsterExecutionInterruptedError, DagsterPipesExecutionError
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import (
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
)
from dagster._core.pipes.context import PipesSession
from dagster._core.pipes.utils import open_pipes_session
from dagster_pipes import PipesExtras
from dagster_shared.record import record
from prefect.client.schemas.objects import State

from dagster_prefect.resource import PrefectResource, is_final_state, is_successful_state

PrefectRunKind = Literal["flow-run", "task-run"]


@record
class PrefectRun:
    """A Prefect run handed off to Prefect, identified well enough to poll and link to.

    `kind` distinguishes the two things Prefect can execute on our behalf, which are
    separate objects in its API and its UI.
    """

    kind: PrefectRunKind
    id: UUID


class BasePipesPrefectClient(PipesClient, TreatAsResourceParam):
    """Shared behavior for launching Prefect work with the Pipes protocol.

    Subclasses supply how the work is launched and how the Pipes bootstrap payload rides
    along with it. Everything after the hand-off — polling for completion, mapping Prefect's
    terminal states onto success or failure, and collecting the reported results — happens
    here so it behaves the same however the work was launched.

    Args:
        prefect (PrefectResource): The Prefect API to launch into and poll.
        context_injector (Optional[PipesContextInjector]): Overrides the subclass's default.
        message_reader (Optional[PipesMessageReader]): Overrides the subclass's default.
        poll_interval_seconds (float): How long to sleep between state checks. Defaults to 5.
        forward_termination (bool): Whether to cancel the Prefect run when the Dagster run is
            terminated. Defaults to True. Only flow runs can actually be cancelled; see
            :py:meth:`_forward_termination`.
    """

    def __init__(
        self,
        prefect: PrefectResource,
        context_injector: PipesContextInjector | None = None,
        message_reader: PipesMessageReader | None = None,
        poll_interval_seconds: float = 5,
        forward_termination: bool = True,
    ):
        self.prefect = check.inst_param(prefect, "prefect", PrefectResource)
        self._context_injector = check.opt_inst_param(
            context_injector, "context_injector", PipesContextInjector
        )
        self._message_reader = check.opt_inst_param(
            message_reader, "message_reader", PipesMessageReader
        )
        self.poll_interval_seconds = check.numeric_param(
            poll_interval_seconds, "poll_interval_seconds"
        )
        self.forward_termination = check.bool_param(forward_termination, "forward_termination")

    def run(
        self,
        *,
        context: OpExecutionContext | AssetExecutionContext,
        extras: PipesExtras | None = None,
        **kwargs,
    ) -> PipesClientCompletedInvocation:
        """Launch Prefect work and block until it reaches a terminal state.

        Raises:
            DagsterPipesExecutionError: The Prefect run finished in any state other than
                completed.
        """
        with open_pipes_session(
            context=context,
            context_injector=self._context_injector or self._default_context_injector(),
            message_reader=self._message_reader or self._default_message_reader(),
            extras=extras,
        ) as session:
            prefect_run = self._launch(context=context, session=session, **kwargs)
            # Logged at launch rather than on completion so a long-running Prefect run can be
            # opened from the Dagster run's logs while it is still going.
            context.log.info(
                f"[pipes] launched Prefect {prefect_run.kind} {prefect_run.id}, waiting for it "
                f"to finish: {self._run_url(prefect_run)}"
            )
            try:
                self._poll_til_final(context, prefect_run)
            except DagsterExecutionInterruptedError:
                if self.forward_termination:
                    self._forward_termination(context, prefect_run)
                raise

        return PipesClientCompletedInvocation(session, metadata=self._dagster_metadata(prefect_run))

    @abstractmethod
    def _launch(
        self,
        *,
        context: OpExecutionContext | AssetExecutionContext,
        session: PipesSession,
        **kwargs,
    ) -> PrefectRun:
        """Start the Prefect work, carrying the session's bootstrap payload along with it."""

    @abstractmethod
    def _default_context_injector(self) -> PipesContextInjector:
        """How the Pipes context reaches the process Prefect runs."""

    @abstractmethod
    def _default_message_reader(self) -> PipesMessageReader:
        """How Pipes messages get back from the process Prefect runs."""

    def _poll_til_final(
        self, context: OpExecutionContext | AssetExecutionContext, prefect_run: PrefectRun
    ) -> None:
        last_reported_type = None
        while True:
            state = self._read_state(prefect_run)

            state_type = state.type if state else None
            if state_type != last_reported_type:
                context.log.info(
                    f"[pipes] Prefect {prefect_run.kind} {prefect_run.id} is {state_type}"
                )
                last_reported_type = state_type

            if is_final_state(state):
                if not is_successful_state(state):
                    raise DagsterPipesExecutionError(
                        f"Prefect {prefect_run.kind} {prefect_run.id} finished as "
                        f"{state_type}: {_state_message(state)}"
                    )
                return

            time.sleep(self.poll_interval_seconds)

    def _read_state(self, prefect_run: PrefectRun) -> State | None:
        if prefect_run.kind == "flow-run":
            return self.prefect.get_flow_run(prefect_run.id).state
        return self.prefect.get_task_run(prefect_run.id).state

    def _forward_termination(
        self, context: OpExecutionContext | AssetExecutionContext, prefect_run: PrefectRun
    ) -> None:
        """Ask Prefect to cancel the run the Dagster step was waiting on.

        Only flow runs can be cancelled. Prefect's task worker does not act on a cancellation
        request: the task run moves to `CANCELLING`, the worker runs the task to completion
        anyway, and the resulting terminal state overwrites the request. Warning is the honest
        option — writing a state that gets overwritten would only misreport what happened.
        """
        if prefect_run.kind != "flow-run":
            context.log.warning(
                f"[pipes] Dagster run terminated, but Prefect {prefect_run.kind} "
                f"{prefect_run.id} cannot be cancelled: Prefect's task worker runs a task to "
                "completion regardless. It will keep running."
            )
            return

        context.log.info(
            f"[pipes] Dagster run terminated, cancelling Prefect {prefect_run.kind} "
            f"{prefect_run.id}"
        )
        # Returns as soon as Prefect accepts the request. The worker moves the run from
        # CANCELLING to CANCELLED on its own schedule, and blocking on that would hold up
        # Dagster's own termination.
        self.prefect.cancel_flow_run(prefect_run.id)

    def _run_url(self, prefect_run: PrefectRun) -> str:
        if prefect_run.kind == "flow-run":
            return self.prefect.flow_run_url(prefect_run.id)
        return self.prefect.task_run_url(prefect_run.id)

    def _dagster_metadata(self, prefect_run: PrefectRun) -> RawMetadataMapping:
        """Metadata attached to every result the session reports.

        Keys stay the same whichever way the work was launched, so a run is findable by the
        same metadata whether it was a task or a deployment.
        """
        return {
            "Prefect Run ID": str(prefect_run.id),
            "Prefect Run URL": UrlMetadataValue(self._run_url(prefect_run)),
        }


def _state_message(state: State | None) -> str:
    # Prefect leaves `message` empty on plenty of terminal states, so fall back to the name
    # rather than reporting a failure with nothing in it.
    if state is None:
        return "no state reported"
    return state.message or state.name or str(state.type)
