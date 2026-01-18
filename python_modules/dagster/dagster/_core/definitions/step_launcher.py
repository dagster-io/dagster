from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping
from typing import TYPE_CHECKING, NamedTuple, Optional

import dagster._check as check
from dagster._annotations import superseded
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.execution.retries import RetryMode
from dagster._core.storage.dagster_run import DagsterRun

if TYPE_CHECKING:
    from dagster._core.events import DagsterEvent
    from dagster._core.execution.context.system import StepExecutionContext
    from dagster._core.execution.plan.state import KnownExecutionState


class StepRunRef(
    NamedTuple(
        "_StepRunRef",
        [
            ("run_config", Mapping[str, object]),
            ("dagster_run", DagsterRun),
            ("run_id", str),
            ("retry_mode", RetryMode),
            ("step_key", str),
            ("recon_job", ReconstructableJob),
            ("known_state", Optional["KnownExecutionState"]),
        ],
    )
):
    """A serializable object that specifies what's needed to hydrate a step so
    that it can be executed in a process outside the plan process.

    Users should not instantiate this class directly.
    """

    def __new__(
        cls,
        run_config: Mapping[str, object],
        dagster_run: DagsterRun,
        run_id: str,
        retry_mode: RetryMode,
        step_key: str,
        recon_job: ReconstructableJob,
        known_state: Optional["KnownExecutionState"],
    ):
        from dagster._core.execution.plan.state import KnownExecutionState

        return super().__new__(
            cls,
            check.mapping_param(run_config, "run_config", key_type=str),
            check.inst_param(dagster_run, "dagster_run", DagsterRun),
            check.str_param(run_id, "run_id"),
            check.inst_param(retry_mode, "retry_mode", RetryMode),
            check.str_param(step_key, "step_key"),
            check.inst_param(recon_job, "recon_job", ReconstructableJob),
            check.opt_inst_param(known_state, "known_state", KnownExecutionState),
        )


_step_launcher_supersession = superseded(
    subject="StepLauncher",
    additional_warn_text="While there is no plan to remove this functionality, for new projects, we recommend using Dagster Pipes. For more information, see https://docs.dagster.io/guides/build/external-pipelines",
)


@_step_launcher_supersession
class StepLauncher(ABC):
    """A StepLauncher is responsible for executing steps, either in-process or in an external process."""

    @abstractmethod
    def launch_step(self, step_context: "StepExecutionContext") -> Iterator["DagsterEvent"]:
        """Args:
            step_context (StepExecutionContext): The context that we're executing the step in.

        Returns:
            Iterator[DagsterEvent]: The events for the step.
        """
