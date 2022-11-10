from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Mapping, NamedTuple, Optional

import dagster._check as check
from dagster._core.definitions.reconstruct import ReconstructablePipeline
from dagster._core.execution.retries import RetryMode
from dagster._core.storage.pipeline_run import PipelineRun

if TYPE_CHECKING:
    from dagster._core.execution.plan.state import KnownExecutionState


class StepRunRef(
    NamedTuple(
        "_StepRunRef",
        [
            ("run_config", Mapping[str, object]),
            ("pipeline_run", PipelineRun),
            ("run_id", str),
            ("retry_mode", RetryMode),
            ("step_key", str),
            ("recon_pipeline", ReconstructablePipeline),
            ("known_state", Optional["KnownExecutionState"]),
        ],
    )
):
    """
    A serializable object that specifies what's needed to hydrate a step so
    that it can be executed in a process outside the plan process.

    Users should not instantiate this class directly.
    """

    def __new__(
        cls,
        run_config: Mapping[str, object],
        pipeline_run: PipelineRun,
        run_id: str,
        retry_mode: RetryMode,
        step_key: str,
        recon_pipeline: ReconstructablePipeline,
        known_state: Optional["KnownExecutionState"],
    ):
        from dagster._core.execution.plan.state import KnownExecutionState

        return super(StepRunRef, cls).__new__(
            cls,
            check.mapping_param(run_config, "run_config", key_type=str),
            check.inst_param(pipeline_run, "pipeline_run", PipelineRun),
            check.str_param(run_id, "run_id"),
            check.inst_param(retry_mode, "retry_mode", RetryMode),
            check.str_param(step_key, "step_key"),
            check.inst_param(recon_pipeline, "recon_pipeline", ReconstructablePipeline),
            check.opt_inst_param(known_state, "known_state", KnownExecutionState),
        )


class StepLauncher(ABC):
    """
    A StepLauncher is responsible for executing steps, either in-process or in an external process.
    """

    @abstractmethod
    def launch_step(self, step_context):
        """
        Args:
            step_context (StepExecutionContext): The context that we're executing the step in.

        Returns:
            Iterator[DagsterEvent]: The events for the step.
        """
