import time

from celery import Celery

from dagster import check
from dagster.core.engine.engine_base import Engine
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple

from .config import CeleryConfig
from .tasks import create_task

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

        app = Celery('dagster', **(celery_config._asdict()))

        pending_steps = execution_plan.execution_deps()

        task_signatures = {}  # Dict[step_key, celery.Signature]

        for step_key in execution_plan.step_keys_to_execute:
            # This is where we'll eventually set the priority and queue using task_kwargs and tags
            # on the solids
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

        step_results = {}  # Dict[ExecutionStep, celery.AsyncResult]
        completed_steps = set({})  # Set[step_key]

        while pending_steps or step_results:

            results_to_pop = []
            for step_key, result in step_results.items():
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
                    step_results[step_key] = task_signatures[step_key].apply_async()

                    pending_to_pop.append(step_key)

            for step_key in pending_to_pop:
                if step_key in pending_steps:
                    del pending_steps[step_key]

            time.sleep(TICK_SECONDS)
