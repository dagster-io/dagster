import sys
import time

from dagster import check
from dagster.core.engine.engine_base import Engine
from dagster.core.errors import DagsterSubprocessError
from dagster.core.events import DagsterEvent, EngineEventData
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.net import is_local_uri

from .config import CeleryConfig
from .defaults import task_default_priority, task_default_queue

TICK_SECONDS = 1
DELEGATE_MARKER = 'celery_queue_wait'


class CeleryEngine(Engine):
    @staticmethod
    def execute(pipeline_context, execution_plan):
        from .tasks import make_app

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

        storage = pipeline_context.environment_dict.get('storage')

        if (celery_config.broker and not is_local_uri(celery_config.broker)) or (
            celery_config.backend and not is_local_uri(celery_config.backend)
        ):
            check.invariant(
                storage.get('s3') or storage.get('gcs'),
                'Must use S3 or GCS storage with non-local Celery broker: {broker} '
                'and backend: {backend}'.format(
                    broker=celery_config.broker, backend=celery_config.backend
                ),
            )
        else:
            check.invariant(
                not storage.get('in_memory'),
                'Cannot use in-memory storage with Celery, use filesystem, S3, or GCS',
            )

        app = make_app(celery_config)

        priority_for_step = lambda step: (
            -1 * int(step.tags.get('dagster-celery/priority', task_default_priority))
            + -1 * _get_run_priority(pipeline_context)
        )
        priority_for_key = lambda step_key: (
            priority_for_step(execution_plan.get_step_by_key(step_key))
        )
        _warn_on_priority_misuse(pipeline_context, execution_plan)

        step_results = {}  # Dict[ExecutionStep, celery.AsyncResult]
        step_errors = {}
        completed_steps = set({})  # Set[step_key]
        active_execution = execution_plan.start(
            retries=pipeline_context.executor_config.retries, sort_key_fn=priority_for_step
        )
        stopping = False

        while (not active_execution.is_complete and not stopping) or step_results:

            results_to_pop = []
            for step_key, result in sorted(
                step_results.items(), key=lambda x: priority_for_key(x[0])
            ):
                if result.ready():
                    try:
                        step_events = result.get()
                    except Exception as e:  # pylint: disable=broad-except
                        # We will want to do more to handle the exception here.. maybe subclass Task
                        # Certainly yield an engine or pipeline event
                        step_events = []
                        step_errors[step_key] = serializable_error_info_from_exc_info(
                            sys.exc_info()
                        )
                        stopping = True
                    for step_event in step_events:
                        event = deserialize_json_to_dagster_namedtuple(step_event)
                        yield event
                        active_execution.handle_event(event)

                    results_to_pop.append(step_key)
                    completed_steps.add(step_key)

            for step_key in results_to_pop:
                if step_key in step_results:
                    del step_results[step_key]
                    active_execution.verify_complete(pipeline_context, step_key)

            # process skips from failures or uncovered inputs
            for event in active_execution.skipped_step_events_iterator(pipeline_context):
                yield event

            # don't add any new steps if we are stopping
            if stopping:
                continue

            # This is a slight refinement. If we have n workers idle and schedule m > n steps for
            # execution, the first n steps will be picked up by the idle workers in the order in
            # which they are scheduled (and the following m-n steps will be executed in priority
            # order, provided that it takes longer to execute a step than to schedule it). The test
            # case has m >> n to exhibit this behavior in the absence of this sort step.
            for step in active_execution.get_steps_to_execute():
                try:
                    queue = step.tags.get('dagster-celery/queue', task_default_queue)
                    yield DagsterEvent.engine_event(
                        pipeline_context,
                        'Submitting celery task for step "{step_key}" to queue "{queue}".'.format(
                            step_key=step.key, queue=queue
                        ),
                        EngineEventData(marker_start=DELEGATE_MARKER),
                        step_key=step.key,
                    )
                    step_results[step.key] = _submit_task(app, pipeline_context, step, queue)
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

        if step_errors:
            raise DagsterSubprocessError(
                'During celery execution errors occurred in workers:\n{error_list}'.format(
                    error_list='\n'.join(
                        [
                            '[{step}]: {err}'.format(step=key, err=err.to_string())
                            for key, err in step_errors.items()
                        ]
                    )
                ),
                subprocess_error_infos=list(step_errors.values()),
            )


def _submit_task(app, pipeline_context, step, queue):
    from .tasks import create_task

    run_priority = _get_run_priority(pipeline_context)
    step_priority = int(step.tags.get('dagster-celery/priority', task_default_priority))
    priority = run_priority + step_priority

    task = create_task(app)

    task_signature = task.si(
        instance_ref_dict=pipeline_context.instance.get_ref().to_dict(),
        handle_dict=pipeline_context.execution_target_handle.to_dict(),
        run_id=pipeline_context.pipeline_run.run_id,
        step_keys=[step.key],
        retries_dict=pipeline_context.executor_config.retries.for_inner_plan().to_config(),
    )
    return task_signature.apply_async(
        priority=priority, queue=queue, routing_key='{queue}.execute_plan'.format(queue=queue),
    )


def _get_run_priority(context):
    if not context.has_tag('dagster-celery/run_priority'):
        return 0
    try:
        return int(context.get_tag('dagster-celery/run_priority'))
    except ValueError:
        return 0


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
