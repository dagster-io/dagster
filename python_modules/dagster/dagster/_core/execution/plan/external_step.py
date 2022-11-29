import os
import pickle
import shutil
import subprocess
import sys
from typing import TYPE_CHECKING, Callable, Iterator, Optional, cast

import dagster._check as check
from dagster._config import Field, StringSource
from dagster._core.code_pointer import FileCodePointer, ModuleCodePointer
from dagster._core.definitions.reconstruct import ReconstructablePipeline, ReconstructableRepository
from dagster._core.definitions.resource_definition import resource
from dagster._core.definitions.step_launcher import StepLauncher, StepRunRef
from dagster._core.errors import raise_execution_interrupts
from dagster._core.events import DagsterEvent
from dagster._core.events.log import EventLogEntry
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.context.system import StepExecutionContext
from dagster._core.execution.context_creation_pipeline import PlanExecutionContextManager
from dagster._core.execution.plan.execute_plan import dagster_event_sequence_for_step
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.instance import DagsterInstance
from dagster._core.storage.file_manager import LocalFileHandle, LocalFileManager
from dagster._serdes import deserialize_value

PICKLED_EVENTS_FILE_NAME = "events.pkl"
PICKLED_STEP_RUN_REF_FILE_NAME = "step_run_ref.pkl"

if TYPE_CHECKING:
    from dagster._core.execution.plan.step import ExecutionStep


@resource(
    config_schema={
        "scratch_dir": Field(
            StringSource,  # type: ignore  # (mypy bug)
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
        self,
        step_context: StepExecutionContext,
    ) -> Iterator[DagsterEvent]:
        step_run_ref = step_context_to_step_run_ref(step_context)
        run_id = step_context.pipeline_run.run_id

        step_run_dir = os.path.join(self.scratch_dir, run_id, step_run_ref.step_key)
        if os.path.exists(step_run_dir):
            shutil.rmtree(step_run_dir)
        os.makedirs(step_run_dir)

        step_run_ref_file_path = os.path.join(step_run_dir, PICKLED_STEP_RUN_REF_FILE_NAME)
        with open(step_run_ref_file_path, "wb") as step_pickle_file:
            pickle.dump(step_run_ref, step_pickle_file)

        command_tokens = [
            sys.executable,
            "-m",
            "dagster._core.execution.plan.local_external_step_main",
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
        all_events = deserialize_value(pickle.loads(events_data))

        for event in all_events:
            # write each pickled event from the external instance to the local instance
            step_context.instance.handle_new_event(event)
            if event.is_dagster_event:
                yield event.dagster_event


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
    step_context: StepExecutionContext,
    package_dir: Optional[str] = None,
) -> StepRunRef:
    """
    Args:
        step_context (StepExecutionContext): The step context.
        package_dir (Optional[str]): If set, the reconstruction file code pointer will be converted
            to be relative a module pointer relative to the package root.  This enables executing
            steps in remote setups where the package containing the pipeline resides at a different
            location on the filesystem in the remote environment than in the environment executing
            the plan process.

    Returns (StepRunRef):
        A reference to the step.
    """

    check.inst_param(step_context, "step_context", StepExecutionContext)

    retry_mode = step_context.retry_mode

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
                        working_directory=os.getcwd(),
                    ),
                    container_image=recon_pipeline.repository.container_image,
                    executable_path=recon_pipeline.repository.executable_path,
                    entry_point=recon_pipeline.repository.entry_point,
                    container_context=recon_pipeline.repository.container_context,
                    repository_load_data=step_context.plan_data.execution_plan.repository_load_data,
                ),
                pipeline_name=recon_pipeline.pipeline_name,
                solids_to_execute=recon_pipeline.solids_to_execute,
            )

    return StepRunRef(
        run_config=step_context.run_config,
        pipeline_run=step_context.pipeline_run,
        run_id=step_context.pipeline_run.run_id,
        step_key=step_context.step.key,
        retry_mode=retry_mode,
        recon_pipeline=recon_pipeline,  # type: ignore
        known_state=step_context.get_known_state(),
    )


def external_instance_from_step_run_ref(
    step_run_ref: StepRunRef, event_listener_fn: Optional[Callable[[EventLogEntry], object]] = None
) -> DagsterInstance:
    """
    Create an ephemeral DagsterInstance that is suitable for executing steps that are specified
    by a StepRunRef by pre-populating certain values.

    Args:
        step_run_ref (StepRunRef): The reference to the the step that we want to execute
        event_listener_fn (EventLogEntry -> Any): A function that handles each individual
            EventLogEntry created on this instance. Generally used to send these events back to
            the host instance.
    Returns:
        DagsterInstance: A DagsterInstance that can be used to execute an external step.
    """
    instance = DagsterInstance.ephemeral()
    if event_listener_fn:
        instance.add_event_listener(step_run_ref.run_id, event_listener_fn)
    return instance


def step_run_ref_to_step_context(
    step_run_ref: StepRunRef, instance: DagsterInstance
) -> StepExecutionContext:
    check.inst_param(instance, "instance", DagsterInstance)

    pipeline = step_run_ref.recon_pipeline

    solids_to_execute = step_run_ref.pipeline_run.solids_to_execute
    if solids_to_execute or step_run_ref.pipeline_run.asset_selection:
        pipeline = step_run_ref.recon_pipeline.subset_for_execution_from_existing_pipeline(
            frozenset(solids_to_execute) if solids_to_execute else None,
            asset_selection=step_run_ref.pipeline_run.asset_selection,
        )

    execution_plan = create_execution_plan(
        pipeline,
        step_run_ref.run_config,
        mode=step_run_ref.pipeline_run.mode,
        step_keys_to_execute=[step_run_ref.step_key],
        known_state=step_run_ref.known_state,
        # we packaged repository_load_data onto the reconstructable pipeline when creating the
        # StepRunRef, rather than putting it in a separate field
        repository_load_data=pipeline.repository.repository_load_data,
    )

    initialization_manager = PlanExecutionContextManager(
        retry_mode=step_run_ref.retry_mode.for_inner_plan(),
        pipeline=pipeline,
        execution_plan=execution_plan,
        run_config=step_run_ref.run_config,
        pipeline_run=step_run_ref.pipeline_run,
        instance=instance,
    )
    for _ in initialization_manager.prepare_context():
        pass
    execution_context = initialization_manager.get_context()

    execution_step = cast("ExecutionStep", execution_plan.get_step_by_key(step_run_ref.step_key))

    step_execution_context = execution_context.for_step(
        execution_step,
        step_run_ref.known_state or KnownExecutionState(),
    )
    # Since for_step is abstract for IPlanContext, its return type is IStepContext.
    # Since we are launching from a PlanExecutionContext, the type will always be
    # StepExecutionContext.
    step_execution_context = cast(StepExecutionContext, step_execution_context)

    return step_execution_context


def run_step_from_ref(
    step_run_ref: StepRunRef, instance: DagsterInstance
) -> Iterator[DagsterEvent]:
    check.inst_param(instance, "instance", DagsterInstance)
    step_context = step_run_ref_to_step_context(step_run_ref, instance)

    # The step should be forced to run locally with respect to the remote process that this step
    # context is being deserialized in
    return dagster_event_sequence_for_step(step_context, force_local_execution=True)
