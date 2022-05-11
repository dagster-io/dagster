from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from dagster import DagsterEvent, DagsterInstance
from dagster import _check as check
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.grpc.types import ExecuteStepArgs


class StepHandlerContext:
    def __init__(
        self,
        instance: DagsterInstance,
        execute_step_args: ExecuteStepArgs,
        step_tags: Dict[str, Dict[str, str]],
        pipeline_run: Optional[PipelineRun] = None,
    ) -> None:
        self._instance = instance
        self._execute_step_args = execute_step_args
        self._step_tags = step_tags
        self._pipeline_run = pipeline_run

    @property
    def execute_step_args(self) -> ExecuteStepArgs:
        return self._execute_step_args

    @property
    def pipeline_run(self) -> PipelineRun:
        # lazy load
        if not self._pipeline_run:
            run_id = self.execute_step_args.pipeline_run_id
            run = self._instance.get_run_by_id(run_id)
            if run is None:
                check.failed(f"Failed to load run {run_id}")
            self._pipeline_run = run

        return self._pipeline_run

    @property
    def step_tags(self) -> Dict[str, Dict[str, str]]:
        return self._step_tags

    @property
    def instance(self) -> DagsterInstance:
        return self._instance


class StepHandler(ABC):  # pylint: disable=no-init
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def launch_step(self, step_handler_context: StepHandlerContext) -> List[DagsterEvent]:
        pass

    @abstractmethod
    def check_step_health(self, step_handler_context: StepHandlerContext) -> List[DagsterEvent]:
        pass

    @abstractmethod
    def terminate_step(self, step_handler_context: StepHandlerContext) -> List[DagsterEvent]:
        pass
