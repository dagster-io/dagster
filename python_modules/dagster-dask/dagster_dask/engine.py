import itertools

import dask
import dask.distributed

from dagster import check
from dagster.core.engine.engine_base import IEngine

from dagster.core.events import DagsterEvent
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.plan import ExecutionPlan

from dagster_graphql.cli import execute_query
from dagster_graphql.util import (
    dagster_event_from_dict,
    get_log_message_event_fragment,
    get_step_event_fragment,
)

from .config import DaskConfig
from .query import QUERY_TEMPLATE


def query_on_dask_worker(handle, query, variables, dependencies):  # pylint: disable=unused-argument
    '''Note that we need to pass "dependencies" to ensure Dask sequences futures during task
    scheduling, even though we do not use this argument within the function.

    We also pass in 'raise_on_error' here, because otherwise (currently) very little information
    is propagated to the dask master from the workers about the state of execution; we should at
    least inform the user of exceptions.
    '''
    res = execute_query(handle, query, variables, raise_on_error=True, use_sync_executor=True)
    handle_errors(res)
    return handle_result(res)


def handle_errors(res):
    if res.get('errors'):
        raise Exception('Internal error in GraphQL request. Response: {}'.format(res))

    if not res.get('data', {}).get('startPipelineExecution', {}).get('__typename'):
        raise Exception('Unexpected response type. Response: {}'.format(res))


def handle_result(res):
    res_data = res['data']['startPipelineExecution']

    res_type = res_data['__typename']

    if res_type == 'InvalidStepError':
        raise Exception('invalid step {step_key}'.format(step_key=res_data['invalidStepKey']))

    if res_type == 'InvalidOutputError':
        raise Exception(
            'invalid output {output} for step {step_key}'.format(
                output=res_data['invalidOutputName'], step_key=res_data['stepKey']
            )
        )

    if res_type == 'PipelineConfigValidationInvalid':
        errors = [err['message'] for err in res_data['errors']]
        raise Exception(
            'Pipeline configuration invalid:\n{errors}'.format(errors='\n'.join(errors))
        )

    if res_type == 'PipelineNotFoundError':
        raise Exception(
            'Pipeline "{pipeline_name}" not found: {message}:'.format(
                pipeline_name=res_data['pipelineName'], message=res_data['message']
            )
        )

    if res_type == 'PythonError':
        raise Exception(
            'Subplan execution failed: {message}\n{stack}'.format(
                message=res_data['message'], stack=res_data['stack']
            )
        )

    if res_type == 'StartPipelineExecutionSuccess':
        pipeline_name = res_data['run']['pipeline']['name']

        skip_events = {
            'LogMessageEvent',
            'PipelineStartEvent',
            'PipelineSuccessEvent',
            'PipelineInitFailureEvent',
            'PipelineFailureEvent',
        }

        return [
            dagster_event_from_dict(e, pipeline_name)
            for e in res_data['run']['logs']['nodes']
            if e['__typename'] not in skip_events
        ]

    raise Exception('unexpected result type')


def build_graphql_query():
    log_message_event_fragment = get_log_message_event_fragment()
    step_event_fragment = get_step_event_fragment()

    return '\n'.join(
        (
            QUERY_TEMPLATE.format(
                step_event_fragment=step_event_fragment.include_key,
                log_message_event_fragment=log_message_event_fragment.include_key,
            ),
            step_event_fragment.fragment,
            log_message_event_fragment.fragment,
        )
    )


class DaskEngine(IEngine):  # pylint: disable=no-init
    @staticmethod
    def execute(pipeline_context, execution_plan, step_keys_to_execute=None):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        step_key_set = None if step_keys_to_execute is None else set(step_keys_to_execute)

        dask_config = pipeline_context.run_config.executor_config

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

        query = build_graphql_query()

        pipeline_name = pipeline_context.pipeline_def.name

        with dask.distributed.Client(**dask_config.build_dict(pipeline_name)) as client:
            execution_futures = []
            execution_futures_dict = {}

            for step_level in step_levels:
                for step in step_level:
                    if step_key_set and step.key not in step_key_set:
                        continue

                    step_context = pipeline_context.for_step(step)

                    check.invariant(
                        not step_context.run_config.loggers,
                        'Cannot inject loggers via RunConfig with the Dask executor',
                    )

                    check.invariant(
                        not step_context.event_callback,
                        'Cannot use event_callback with Dask executor',
                    )

                    # We ensure correctness in sequencing by letting Dask schedule futures and
                    # awaiting dependencies within each step.
                    dependencies = [
                        execution_futures_dict[ni.prev_output_handle.step_key]
                        for ni in step.step_inputs
                    ]

                    variables = {
                        'executionParams': {
                            'selector': {'name': pipeline_name},
                            'environmentConfigData': pipeline_context.environment_dict,
                            'mode': pipeline_context.mode_def.name,
                            'executionMetadata': {'runId': pipeline_context.run_config.run_id},
                            'stepKeys': [step.key],
                        }
                    }

                    dask_task_name = '%s.%s' % (pipeline_name, step.key)

                    future = client.submit(
                        query_on_dask_worker,
                        pipeline_context.execution_target_handle,
                        query,
                        variables,
                        dependencies,
                        key=dask_task_name,
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
