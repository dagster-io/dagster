from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Mapping, NamedTuple, Optional, Sequence

import dagster._check as check
from dagster.core.definitions.reconstruct import ReconstructablePipeline
from dagster.core.execution.retries import RetryMode
from dagster.core.storage.pipeline_run import PipelineRun

if TYPE_CHECKING:
    from dagster.core.events.log import EventLogEntry
    from dagster.core.execution.plan.state import KnownExecutionState


class StepRunRef(
    NamedTuple(
        "_StepRunRef",
        [
            ("run_config", Dict[str, object]),
            ("pipeline_run", PipelineRun),
            ("run_id", str),
            ("retry_mode", RetryMode),
            ("step_key", str),
            ("recon_pipeline", ReconstructablePipeline),
            ("prior_attempts_count", int),
            ("known_state", Optional["KnownExecutionState"]),
            ("run_group", Sequence[PipelineRun]),
            ("upstream_output_events", Sequence["EventLogEntry"]),
        ],
    )
):
    """
    A serializable object that specifies what's needed to hydrate a step so that it can
    be executed in a process outside the plan process.
    """

    def __new__(
        cls,
        run_config: Mapping[str, object],
        pipeline_run: PipelineRun,
        run_id: str,
        retry_mode: RetryMode,
        step_key: str,
        recon_pipeline: ReconstructablePipeline,
        prior_attempts_count: int,
        known_state: Optional["KnownExecutionState"],
        run_group: Optional[Sequence[PipelineRun]],
        upstream_output_events: Optional[Sequence["EventLogEntry"]],
    ):
        from dagster.core.execution.plan.state import KnownExecutionState
        from dagster.core.storage.event_log import EventLogEntry

        return super(StepRunRef, cls).__new__(
            cls,
            check.dict_param(run_config, "run_config", key_type=str),
            check.inst_param(pipeline_run, "pipeline_run", PipelineRun),
            check.str_param(run_id, "run_id"),
            check.inst_param(retry_mode, "retry_mode", RetryMode),
            check.str_param(step_key, "step_key"),
            check.inst_param(recon_pipeline, "recon_pipeline", ReconstructablePipeline),
            check.int_param(prior_attempts_count, "prior_attempts_count"),
            check.opt_inst_param(known_state, "known_state", KnownExecutionState),
            check.opt_list_param(run_group, "run_group", of_type=PipelineRun),
            check.opt_list_param(
                upstream_output_events, "upstream_output_events", of_type=EventLogEntry
            ),
        )


class StepLauncher(ABC):
    """
    A StepLauncher is responsible for executing steps, either in-process or in an external process.
    """

    @abstractmethod
    def launch_step(self, step_context, prior_attempts_count):
        """
        Args:
            step_context (StepExecutionContext): The context that we're executing the step in.
            prior_attempts_count (int): The number of times this step has been attempted in the same run.

        Returns:
            Iterator[DagsterEvent]: The events for the step.
        """
