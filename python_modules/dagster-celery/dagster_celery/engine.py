import sys
import time
from collections import defaultdict

from dagster import check
from dagster.core.engine.engine_base import Engine
from dagster.core.events import DagsterEvent, EngineEventData
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple
from dagster.utils.error import serializable_error_info_from_exc_info

from .config import CeleryConfig
from .defaults import task_default_priority, task_default_queue
from .tasks import create_task, make_app

TICK_SECONDS = 1


class CeleryEngine(Engine):
    @staticmethod
    def execute(pipeline_context, execution_plan):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)

        check.param_invariant(
            isinstance(pipeline_context.executor_config, CeleryConfig),
            'pipeline_context',
            'Expected executor_config to be CeleryConfig got {}'.format(
                pipeline_context.executor_config
            ),
        )

        celery_config = pipeline_context.executor_config

        pipeline_name = pipeline_context.pipeline_def.name

        handle_dict = pipeline_context.execution_target_handle.to_dict()

        instance_ref_dict = pipeline_context.instance.get_ref().to_dict()

        environment_dict = dict(pipeline_context.environment_dict, execution={'in_process': {}})

        mode = pipeline_context.mode_def.name

        run_id = pipeline_context.pipeline_run.run_id

        app = make_app(celery_config)

        task_signatures = {}  # Dict[step_key, celery.Signature]
        apply_kwargs = defaultdict(dict)  # Dict[step_key, Dict[str, Any]]

        priority_for_step = lambda step: (
            -1 * int(step.tags.get('dagster-celery/priority', task_default_priority))
        )
        priority_for_key = lambda step_key: (-1 * apply_kwargs[step_key]['priority'])
        _warn_on_priority_misuse(pipeline_context, execution_plan)

        for step_key in execution_plan.step_keys_to_execute:
            step = execution_plan.get_step_by_key(step_key)
            priority = int(step.tags.get('dagster-celery/priority', task_default_priority))
            queue = step.tags.get('dagster-celery/queue', task_default_queue)
            task = create_task(app)

            variables = {
                'executionParams': {
                    'selector': {'name': pipeline_name},
                    'environmentConfigData': environment_dict,
                    'mode': mode,
                    'executionMetadata': {'runId': run_id},
                    'stepKeys': [step_key],
                }
            }
            task_signatures[step_key] = task.si(handle_dict, variables, instance_ref_dict)
            apply_kwargs[step_key] = {
                'priority': priority,
                'queue': queue,
                'routing_key': '{queue}.execute_query'.format(queue=queue),
            }

        step_results = {}  # Dict[ExecutionStep, celery.AsyncResult]
        completed_steps = set({})  # Set[step_key]
        active_execution = execution_plan.start(sort_key_fn=priority_for_step)

        while not active_execution.is_complete or step_results:
            results_to_pop = []
            for step_key, result in sorted(
                step_results.items(), key=lambda x: priority_for_key(x[0])
            ):
                if result.ready():
                    try:
                        step_events = result.get()
                    except Exception:  # pylint: disable=broad-except
                        # We will want to do more to handle the exception here.. maybe subclass Task
                        # Certainly yield an engine or pipeline event
                        step_events = []
                    for step_event in step_events:
                        yield deserialize_json_to_dagster_namedtuple(step_event)
                    results_to_pop.append(step_key)
                    completed_steps.add(step_key)
            for step_key in results_to_pop:
                if step_key in step_results:
                    del step_results[step_key]
                    active_execution.mark_complete(step_key)

            # This is a slight refinement. If we have n workers idle and schedule m > n steps for
            # execution, the first n steps will be picked up by the idle workers in the order in
            # which they are scheduled (and the following m-n steps will be executed in priority
            # order, provided that it takes longer to execute a step than to schedule it). The test
            # case has m >> n to exhibit this behavior in the absence of this sort step.
            for step in active_execution.get_available_steps():
                try:
                    step_results[step.key] = task_signatures[step.key].apply_async(
                        **apply_kwargs[step.key]
                    )
                except Exception:
                    yield DagsterEvent.engine_event(
                        pipeline_context,
                        'Encountered error during celery task submission.'.format(),
                        event_specific_data=EngineEventData.engine_error(
                            serializable_error_info_from_exc_info(sys.exc_info()),
                        ),
                    )
                    raise

            time.sleep(TICK_SECONDS)


def _warn_on_priority_misuse(context, execution_plan):
    bad_keys = []
    for key in execution_plan.step_keys_to_execute:
        step = execution_plan.get_step_by_key(key)
        if (
            step.tags.get('dagster/priority') is not None
            and step.tags.get('dagster-celery/priority') is None
        ):
            bad_keys.append(key)

    if bad_keys:
        context.log.warn(
            'The following steps do not have "dagster-celery/priority" set but do '
            'have "dagster/priority" set which is not applicable for the celery engine: [{}]. '
            'Consider using a function to set both keys.'.format(', '.join(bad_keys))
        )
