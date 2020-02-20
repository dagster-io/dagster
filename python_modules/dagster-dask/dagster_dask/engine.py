import dask
import dask.distributed
from dagster_graphql.client.mutations import execute_execute_plan_mutation

from dagster import check, seven
from dagster.core.engine.engine_base import Engine
from dagster.core.events import DagsterEvent
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.utils import frozentags
from dagster.utils.net import is_local_uri

from .config import DaskConfig

# Dask resource requirements are specified under this key
DASK_RESOURCE_REQUIREMENTS_KEY = 'dagster-dask/resource_requirements'


def query_on_dask_worker(
    handle, variables, dependencies, instance_ref=None
):  # pylint: disable=unused-argument
    '''Note that we need to pass "dependencies" to ensure Dask sequences futures during task
    scheduling, even though we do not use this argument within the function.
    '''
    return execute_execute_plan_mutation(handle, variables, instance_ref=instance_ref)


def get_dask_resource_requirements(tags):
    check.inst_param(tags, 'tags', frozentags)
    req_str = tags.get(DASK_RESOURCE_REQUIREMENTS_KEY)
    if req_str is not None:
        return seven.json.loads(req_str)

    return {}


class DaskEngine(Engine):  # pylint: disable=no-init
    @staticmethod
    def execute(pipeline_context, execution_plan):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)

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

        check.invariant(
            pipeline_context.instance.is_persistent,
            'Dask execution requires a persistent DagsterInstance',
        )

        # Remote
        if dask_config.address and not is_local_uri(dask_config.address):
            check.invariant(
                storage.get('s3') or storage.get('gcs'),
                'Must use S3 or GCS storage with non-local Dask address {dask_address}'.format(
                    dask_address=dask_config.address
                ),
            )
        # Local
        else:
            check.invariant(
                not storage.get('in_memory'),
                'Cannot use in-memory storage with Dask, use filesystem, S3, or GCS',
            )

        step_levels = execution_plan.execution_step_levels()

        pipeline_name = pipeline_context.pipeline_def.name

        instance = pipeline_context.instance

        with dask.distributed.Client(**dask_config.build_dict(pipeline_name)) as client:
            execution_futures = []
            execution_futures_dict = {}

            for step_level in step_levels:
                for step in step_level:
                    # We ensure correctness in sequencing by letting Dask schedule futures and
                    # awaiting dependencies within each step.
                    dependencies = []
                    for step_input in step.step_inputs:
                        for key in step_input.dependency_keys:
                            dependencies.append(execution_futures_dict[key])

                    environment_dict = dict(
                        pipeline_context.environment_dict, execution={'in_process': {}}
                    )
                    variables = {
                        'executionParams': {
                            'selector': {'name': pipeline_name},
                            'environmentConfigData': environment_dict,
                            'mode': pipeline_context.mode_def.name,
                            'executionMetadata': {'runId': pipeline_context.pipeline_run.run_id},
                            'stepKeys': [step.key],
                        }
                    }

                    dask_task_name = '%s.%s' % (pipeline_name, step.key)

                    future = client.submit(
                        query_on_dask_worker,
                        pipeline_context.execution_target_handle,
                        variables,
                        dependencies,
                        instance.get_ref(),
                        key=dask_task_name,
                        resources=get_dask_resource_requirements(step.tags),
                    )

                    execution_futures.append(future)
                    execution_futures_dict[step.key] = future

            # This tells Dask to awaits the step executions and retrieve their results to the
            # master
            for future in dask.distributed.as_completed(execution_futures):
                for step_event in future.result():
                    check.inst(step_event, DagsterEvent)

                    yield step_event
