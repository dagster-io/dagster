import os
import pickle
import subprocess
import sys

from dagster import Field, StringSource, check, resource
from dagster.core.definitions.step_launcher import StepLauncher, StepRunRef
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.context_creation_pipeline import pipeline_initialization_manager
from dagster.core.execution.plan.execute_step import core_dagster_event_sequence_for_step
from dagster.core.instance import DagsterInstance
from dagster.core.storage.file_manager import LocalFileHandle

PICKLED_EVENTS_FILE_NAME = 'events.pkl'
PICKLED_STEP_RUN_REF_FILE_NAME = 'step_run_ref.pkl'


@resource(
    config={
        'scratch_dir': Field(
            StringSource,
            description='Directory used to pass files between the plan process and step process.',
        ),
    },
)
def local_external_step_launcher(context):
    return LocalExternalStepLauncher(**context.resource_config)


class LocalExternalStepLauncher(StepLauncher):
    '''Launches each step in its own local process, outside the plan process.'''

    def __init__(self, scratch_dir):
        self.scratch_dir = check.str_param(scratch_dir, 'scratch_dir')

    def launch_step(self, step_context, prior_attempts_count):
        step_run_ref = step_context_to_step_run_ref(step_context, prior_attempts_count)
        run_id = step_context.pipeline_run.run_id

        step_run_dir = os.path.join(self.scratch_dir, run_id, step_run_ref.step_key)
        os.makedirs(step_run_dir)

        step_run_ref_file_path = os.path.join(step_run_dir, PICKLED_STEP_RUN_REF_FILE_NAME)
        with open(step_run_ref_file_path, 'wb') as step_pickle_file:
            pickle.dump(step_run_ref, step_pickle_file)

        command_tokens = [
            'python',
            '-m',
            'dagster.core.execution.plan.local_external_step_main',
            step_run_ref_file_path,
        ]
        subprocess.call(command_tokens, stdout=sys.stdout, stderr=sys.stderr)

        events_file_path = os.path.join(step_run_dir, PICKLED_EVENTS_FILE_NAME)
        events_file_handle = LocalFileHandle(events_file_path)
        events_data = step_context.file_manager.read_data(events_file_handle)
        events = pickle.loads(events_data)

        for event in events:
            yield event


def step_context_to_step_run_ref(step_context, prior_attempts_count, package_dir=None):
    '''
    Args:
        step_context (SystemStepExecutionContext): The step context.
        prior_attempts_count (int): The number of times this time has been tried before in the same
            pipeline run.
        package_dir (Optional[str]): If set, the execution target will be converted to be relative
            to the package root.  This enables executing steps in remote setups where the package
            containing the pipeline resides at a different location on the filesystem in the remote
            environment than in the environment executing the plan process.

    Returns (StepRunRef):
        A reference to the step.
    '''
    execution_target_handle = step_context.execution_target_handle
    if package_dir:
        execution_target_handle = execution_target_handle.to_module_name_based_handle(package_dir)

    return StepRunRef(
        environment_dict=step_context.environment_dict,
        pipeline_run=step_context.pipeline_run,
        run_id=step_context.pipeline_run.run_id,
        step_key=step_context.step.key,
        executor_config=step_context.executor_config,
        execution_target_handle=execution_target_handle,
        prior_attempts_count=prior_attempts_count,
    )


def step_run_ref_to_step_context(step_run_ref):
    execution_target_handle = step_run_ref.execution_target_handle
    pipeline_def = execution_target_handle.build_pipeline_definition().build_sub_pipeline(
        step_run_ref.pipeline_run.selector.solid_subset
    )

    execution_plan = create_execution_plan(
        pipeline_def, step_run_ref.environment_dict, mode=step_run_ref.pipeline_run.mode
    ).build_subset_plan([step_run_ref.step_key])

    initialization_manager = pipeline_initialization_manager(
        execution_plan,
        step_run_ref.environment_dict,
        step_run_ref.pipeline_run,
        DagsterInstance.ephemeral(),
    )
    for _ in initialization_manager.generate_setup_events():
        pass
    pipeline_context = initialization_manager.get_object()

    retries = step_run_ref.executor_config.retries.for_inner_plan()
    active_execution = execution_plan.start(retries=retries)
    step = active_execution.get_next_step()

    pipeline_context = initialization_manager.get_object()
    return pipeline_context.for_step(step)


def run_step_from_ref(step_run_ref):
    step_context = step_run_ref_to_step_context(step_run_ref)
    return core_dagster_event_sequence_for_step(step_context, step_run_ref.prior_attempts_count)
