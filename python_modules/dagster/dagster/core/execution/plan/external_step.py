import os
import pickle
import subprocess
import sys
from typing import Iterator, Optional

from dagster import Field, StringSource, check, resource
from dagster.core.code_pointer import FileCodePointer, ModuleCodePointer
from dagster.core.definitions.reconstructable import (
    ReconstructablePipeline,
    ReconstructableRepository,
)
from dagster.core.definitions.step_launcher import StepLauncher, StepRunRef
from dagster.core.errors import raise_execution_interrupts
from dagster.core.events import DagsterEvent
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.context.system import SystemStepExecutionContext
from dagster.core.execution.context_creation_pipeline import PlanExecutionContextManager
from dagster.core.execution.plan.execute_step import core_dagster_event_sequence_for_step
from dagster.core.instance import DagsterInstance
from dagster.core.storage.file_manager import LocalFileHandle, LocalFileManager

PICKLED_EVENTS_FILE_NAME = "events.pkl"
PICKLED_STEP_RUN_REF_FILE_NAME = "step_run_ref.pkl"


@resource(
    config_schema={
        "scratch_dir": Field(
            StringSource,
            description="Directory used to pass files between the plan process and step process.",
        ),
    },
)
def local_external_step_launcher(context):
    return LocalExternalStepLauncher(**context.resource_config)


class LocalExternalStepLauncher(StepLauncher):
    """Launches each step in its own local process, outside the plan process."""

    def __init__(self, scratch_dir: str):
        self.scratch_dir = check.str_param(scratch_dir, "scratch_dir")

    def launch_step(
        self, step_context: SystemStepExecutionContext, prior_attempts_count: int
    ) -> Iterator[DagsterEvent]:
        step_run_ref = step_context_to_step_run_ref(step_context, prior_attempts_count)
        run_id = step_context.pipeline_run.run_id

        step_run_dir = os.path.join(self.scratch_dir, run_id, step_run_ref.step_key)
        os.makedirs(step_run_dir)

        step_run_ref_file_path = os.path.join(step_run_dir, PICKLED_STEP_RUN_REF_FILE_NAME)
        with open(step_run_ref_file_path, "wb") as step_pickle_file:
            pickle.dump(step_run_ref, step_pickle_file)

        command_tokens = [
            sys.executable,
            "-m",
            "dagster.core.execution.plan.local_external_step_main",
            step_run_ref_file_path,
        ]
        # If this is being called within a `capture_interrupts` context, allow interrupts
        # while waiting for the subprocess to complete, so that we can terminate slow or
        # hanging steps
        with raise_execution_interrupts():
            subprocess.call(command_tokens, stdout=sys.stdout, stderr=sys.stderr)

        events_file_path = os.path.join(step_run_dir, PICKLED_EVENTS_FILE_NAME)
        file_manager = LocalFileManager(".")
        events_file_handle = LocalFileHandle(events_file_path)
        events_data = file_manager.read_data(events_file_handle)
        events = pickle.loads(events_data)

        yield from events


def _module_in_package_dir(file_path: str, package_dir: str) -> str:
    abs_path = os.path.abspath(file_path)
    abs_package_dir = os.path.abspath(package_dir)
    check.invariant(
        os.path.commonprefix([abs_path, abs_package_dir]) == abs_package_dir,
        "File {abs_path} is not underneath package dir {abs_package_dir}".format(
            abs_path=abs_path,
            abs_package_dir=abs_package_dir,
        ),
    )

    relative_path = os.path.relpath(abs_path, abs_package_dir)
    without_extension, _ = os.path.splitext(relative_path)
    return ".".join(without_extension.split(os.sep))


def step_context_to_step_run_ref(
    step_context: SystemStepExecutionContext,
    prior_attempts_count: int,
    package_dir: Optional[str] = None,
) -> StepRunRef:
    """
    Args:
        step_context (SystemStepExecutionContext): The step context.
        prior_attempts_count (int): The number of times this time has been tried before in the same
            pipeline run.
        package_dir (Optional[str]): If set, the reconstruction file code pointer will be converted
            to be relative a module pointer relative to the package root.  This enables executing
            steps in remote setups where the package containing the pipeline resides at a different
            location on the filesystem in the remote environment than in the environment executing
            the plan process.

    Returns (StepRunRef):
        A reference to the step.
    """

    check.inst_param(step_context, "step_context", SystemStepExecutionContext)
    check.int_param(prior_attempts_count, "prior_attempts_count")

    retries = step_context.retries

    recon_pipeline = step_context.pipeline
    if package_dir:
        if isinstance(recon_pipeline, ReconstructablePipeline) and isinstance(
            recon_pipeline.repository.pointer, FileCodePointer
        ):
            recon_pipeline = ReconstructablePipeline(
                repository=ReconstructableRepository(
                    pointer=ModuleCodePointer(
                        _module_in_package_dir(
                            recon_pipeline.repository.pointer.python_file, package_dir
                        ),
                        recon_pipeline.repository.pointer.fn_name,
                    ),
                ),
                pipeline_name=recon_pipeline.pipeline_name,
                solids_to_execute=recon_pipeline.solids_to_execute,
            )

    return StepRunRef(
        run_config=step_context.run_config,
        pipeline_run=step_context.pipeline_run,
        run_id=step_context.pipeline_run.run_id,
        step_key=step_context.step.key,
        retries=retries,
        recon_pipeline=recon_pipeline,
        prior_attempts_count=prior_attempts_count,
    )


def step_run_ref_to_step_context(
    step_run_ref: StepRunRef, instance: DagsterInstance
) -> SystemStepExecutionContext:
    check.inst_param(instance, "instance", DagsterInstance)
    pipeline = step_run_ref.recon_pipeline.subset_for_execution_from_existing_pipeline(
        step_run_ref.pipeline_run.solids_to_execute
    )

    execution_plan = create_execution_plan(
        pipeline, step_run_ref.run_config, mode=step_run_ref.pipeline_run.mode
    ).build_subset_plan([step_run_ref.step_key])
    retries = step_run_ref.retries.for_inner_plan()

    initialization_manager = PlanExecutionContextManager(
        retries,
        execution_plan,
        step_run_ref.run_config,
        step_run_ref.pipeline_run,
        instance,
    )
    for _ in initialization_manager.prepare_context():
        pass
    execution_context = initialization_manager.get_context()

    return execution_context.for_step(execution_plan.get_step_by_key(step_run_ref.step_key))


def run_step_from_ref(
    step_run_ref: StepRunRef, instance: DagsterInstance
) -> Iterator[DagsterEvent]:
    check.inst_param(instance, "instance", DagsterInstance)
    step_context = step_run_ref_to_step_context(step_run_ref, instance)
    return core_dagster_event_sequence_for_step(step_context, step_run_ref.prior_attempts_count)
