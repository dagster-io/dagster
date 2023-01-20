import subprocess
import sys
from subprocess import CompletedProcess
from typing import Iterator, Optional

from dagster._core.events import DagsterEvent
from dagster._core.execution.context.system import IStepContext
from dagster._core.executor.multi_environment.multi_environment_step_handler import (
    RemoteEnvironmentSingleStepHandler,
)
from dagster._core.executor.step_delegating.step_handler.base import (
    CheckStepHealthResult,
    StepHandlerContext,
)
from dagster._serdes.serdes import serialize_dagster_namedtuple


# This is an example of what an integrator would have to write
# to instigate a step on a remote environment
class PythonScriptSingleStepHandler(RemoteEnvironmentSingleStepHandler):
    def __init__(self, python_script: str, executable: Optional[str] = None):
        self._python_script = python_script
        self._executable: str = executable if executable else sys.executable
        self._result: Optional[CompletedProcess[str]] = None

    def launch_single_step(
        self, step_context: IStepContext, step_handler_context: StepHandlerContext
    ) -> Optional[Iterator[DagsterEvent]]:
        step_key = step_context.step.key
        run_id = step_context.run_id
        ref = step_handler_context.instance.get_ref()
        ref_json = serialize_dagster_namedtuple(ref)

        # For example this could launch a spark job on a remote environment instead
        # Serialization the InstanceRef not necessarily required. For example
        # the other process could new up a DagsterInstance the communicates with
        # Dagster Cloud over HTTP. Run_id and step_key are always required as they
        # are necessary to fetch additional per-step information that we stash
        # in the key value store
        self._result = subprocess.run(
            [sys.executable, self._python_script, run_id, step_key, ref_json],
            stdout=subprocess.PIPE,
            text=True,
        )

        return None

    def terminate_single_step(
        self, _step_context: IStepContext, step_handler_context: StepHandlerContext
    ) -> Optional[Iterator[DagsterEvent]]:
        raise NotImplementedError()

    def check_step_health(
        self, _step_context: IStepContext, _step_handler_context: StepHandlerContext
    ):
        assert self._result
        return CheckStepHealthResult(is_healthy=self._result.returncode == 0)
