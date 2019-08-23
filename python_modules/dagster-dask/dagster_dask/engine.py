import itertools

import dask
import dask.distributed

from dagster import check
from dagster.core.engine.engine_base import IEngine
from dagster.core.events import DagsterEvent
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.plan import ExecutionPlan

from dagster_graphql.client.mutations import execute_start_pipeline_execution_query

from .config import DaskConfig


# Dask resource requirements are specified under this key
DASK_RESOURCE_REQUIREMENTS_KEY = 'dagster-dask/resource_requirements'


def query_on_dask_worker(handle, variables, dependencies):  # pylint: disable=unused-argument
    '''Note that we need to pass "dependencies" to ensure Dask sequences futures during task
    scheduling, even though we do not use this argument within the function.

    We also set 'raise_on_error' within pipeline execution, because otherwise (currently) very
    little information is propagated to the dask master from the workers about the state of
    execution; we should at least inform the user of exceptions.
    '''
    return execute_start_pipeline_execution_query(handle, variables)


class DaskEngine(IEngine):  # pylint: disable=no-init
    @staticmethod
    def execute(pipeline_context, execution_plan, step_keys_to_execute=None):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        step_key_set = None if step_keys_to_execute is None else set(step_keys_to_execute)

        dask_config = pipeline_context.executor_config

        check.param_invariant(
            isinstance(pipeline_context.executor_config, DaskConfig),
            'pipeline_context',
            'Expected executor_config to be DaskConfig got {}'.format(
                pipeline_context.executor_config
            ),
        )

        # Checks to ensure storage is compatible with Dask configuration
        storage = pipeline_context.environment_dict.get('storage')
        check.invariant(storage.keys(), 'Must specify storage to use Dask execution')

        if dask_config.is_remote_execution:
            check.invariant(
                storage.get('s3'),
                'Must use S3 storage with non-local Dask address {dask_address}'.format(
                    dask_address=dask_config.address
                ),
            )
        else:
            check.invariant(
                not storage.get('in_memory'),
                'Cannot use in-memory storage with Dask, use filesystem or S3',
            )

        step_levels = execution_plan.topological_step_levels()

        pipeline_name = pipeline_context.pipeline_def.name

        with dask.distributed.Client(**dask_config.build_dict(pipeline_name)) as client:
            execution_futures = []
            execution_futures_dict = {}

            for step_level in step_levels:
                for step in step_level:
                    if step_key_set and step.key not in step_key_set:
                        continue

                    # We ensure correctness in sequencing by letting Dask schedule futures and
                    # awaiting dependencies within each step.
                    dependencies = []
                    for step_input in step.step_inputs:
                        for key in step_input.dependency_keys:
                            dependencies.append(execution_futures_dict[key])

                    environment_dict = dict(
                        pipeline_context.environment_dict,
                        execution={'in_process': {'config': {'raise_on_error': False}}},
                    )
                    variables = {
                        'executionParams': {
                            'selector': {'name': pipeline_name},
                            'environmentConfigData': environment_dict,
                            'mode': pipeline_context.mode_def.name,
                            'executionMetadata': {'runId': pipeline_context.run_config.run_id},
                            'stepKeys': [step.key],
                        }
                    }

                    dask_task_name = '%s.%s' % (pipeline_name, step.key)

                    future = client.submit(
                        query_on_dask_worker,
                        pipeline_context.execution_target_handle,
                        variables,
                        dependencies,
                        key=dask_task_name,
                        resources=step.metadata.get(DASK_RESOURCE_REQUIREMENTS_KEY, {}),
                    )

                    execution_futures.append(future)
                    execution_futures_dict[step.key] = future

            # This tells Dask to awaits the step executions and retrieve their results to the master
            execution_step_events = client.gather(execution_futures)

            # execution_step_events is now a list of lists, the inner lists contain the dagster
            # events emitted by each step execution
            for step_event in itertools.chain.from_iterable(execution_step_events):
                check.inst(step_event, DagsterEvent)

                yield step_event
