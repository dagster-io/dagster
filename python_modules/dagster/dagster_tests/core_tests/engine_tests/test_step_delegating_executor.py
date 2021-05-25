import subprocess
from typing import List

from dagster import executor, pipeline, reconstructable, solid
from dagster.core.definitions.executor import multiple_process_executor_requirements
from dagster.core.definitions.mode import ModeDefinition
from dagster.core.events import DagsterEvent
from dagster.core.execution.api import execute_pipeline
from dagster.core.executor.step_delegating import StepDelegatingExecutor, StepHandler
from dagster.core.storage.fs_io_manager import fs_io_manager
from dagster.core.test_utils import instance_for_test
from dagster.serdes import serialize_dagster_namedtuple


class TestStepHandler(StepHandler):
    # This step handler waits for all processes to exit, because windows tests flake when processes
    # are left alive when the test ends. Non-test step handlers should not keep their own state in memory.
    processes = []  # type: ignore

    @property
    def name(self):
        return "TestStepHandler"

    def launch_step(self, step_handler_context):
        print("TestStepHandler Launching Step!")  # pylint: disable=print-call
        TestStepHandler.processes.append(
            subprocess.Popen(
                [
                    "dagster",
                    "api",
                    "execute_step",
                    serialize_dagster_namedtuple(step_handler_context.execute_step_args),
                ]
            )
        )
        return []

    def check_step_health(self, step_handler_context) -> List[DagsterEvent]:
        return []

    def terminate_step(self, step_handler_context):
        raise NotImplementedError()

    @classmethod
    def wait_for_processes(cls):
        for p in cls.processes:
            p.wait(timeout=5)


@executor(
    name="test_step_delegating_executor",
    requirements=multiple_process_executor_requirements(),
)
def test_step_delegating_executor(_):
    return StepDelegatingExecutor(
        TestStepHandler(),
    )


@solid
def bar_solid(_):
    return "bar"


@solid
def baz_solid(_, bar):
    return bar * 2


@pipeline(
    mode_defs=[
        ModeDefinition(
            executor_defs=[test_step_delegating_executor],
            resource_defs={"io_manager": fs_io_manager},
        )
    ]
)
def foo_pipline():
    baz_solid(bar_solid())
    bar_solid()


def test_execute():
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(foo_pipline),
            instance=instance,
            run_config={"execution": {"test_step_delegating_executor": {"config": {}}}},
        )
        TestStepHandler.wait_for_processes()

    assert any(
        [
            "Starting execution with step handler TestStepHandler" in event
            for event in result.event_list
        ]
    )
    assert any(["STEP_START" in event for event in result.event_list])
    assert result.success
