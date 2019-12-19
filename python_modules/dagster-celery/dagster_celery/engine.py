import time
from collections import defaultdict

from dagster import check
from dagster.core.engine.engine_base import Engine
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple

from .config import DEFAULT_PRIORITY, DEFAULT_QUEUE, CeleryConfig
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

        pending_steps = execution_plan.execution_deps()

        task_signatures = {}  # Dict[step_key, celery.Signature]
        apply_kwargs = defaultdict(dict)  # Dict[step_key, Dict[str, Any]]

        sort_by_priority = lambda step_key: (-1 * apply_kwargs[step_key]['priority'])

        for step_key in execution_plan.step_keys_to_execute:
            step = execution_plan.get_step_by_key(step_key)
            priority = step.metadata.get('dagster-celery/priority', DEFAULT_PRIORITY)
            queue = step.metadata.get('dagster-celery/queue', DEFAULT_QUEUE)
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

        while pending_steps or step_results:

            results_to_pop = []
            for step_key, result in sorted(
                step_results.items(), key=lambda x: sort_by_priority(x[0])
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

            pending_to_pop = []
            for step_key, requirements in pending_steps.items():
                if requirements.issubset(completed_steps):
                    pending_to_pop.append(step_key)

            # This is a slight refinement. If we have n workers idle and schedule m > n steps for
            # execution, the first n steps will be picked up by the idle workers in the order in
            # which they are scheduled (and the following m-n steps will be executed in priority
            # order, provided that it takes longer to execute a step than to schedule it). The test
            # case has m >> n to exhibit this behavior in the absence of this sort step.
            to_execute = sorted(pending_to_pop, key=sort_by_priority)
            for step_key in to_execute:
                step_results[step_key] = task_signatures[step_key].apply_async(
                    **apply_kwargs[step_key]
                )

            for step_key in pending_to_pop:
                if step_key in pending_steps:
                    del pending_steps[step_key]

            time.sleep(TICK_SECONDS)
