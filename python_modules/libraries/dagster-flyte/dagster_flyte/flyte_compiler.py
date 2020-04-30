import datetime
import sys
from collections import OrderedDict

from flytekit.common import constants
from flytekit.common.tasks import sdk_runnable
from flytekit.common.workflow import SdkWorkflow

from dagster import PipelineDefinition, check
from dagster.core.execution.api import create_execution_plan, execute_plan_iterator
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.instance import DagsterInstance


class DagsterFlyteCompiler:
    def __init__(self, pipeline, environment_dict):
        check.inst(pipeline, PipelineDefinition)
        check.inst(environment_dict, dict)

        self.pipeline = pipeline
        self.environment_dict = environment_dict
        self.sdk_node_dict = OrderedDict()

    def __call__(self, module='__main__'):
        """
        Creates an SdkWorkflow from a dagster pipeline. Then, adds the nodes as attrs within the module
        that this function is invoked from. User will need to manually provide the module name.
        This is required because flytekit runs dir() on the module that the resultant container
        registers, in order  to discover the DAG structure.
        """

        self.get_flyte_sdk_workflow()
        for name, node in self.get_sdk_tasks():
            setattr(sys.modules[module], name, node)

        return SdkWorkflow(
            inputs=[],
            outputs=[],
            nodes=sorted(
                [node().assign_id_and_return(name) for name, node in self.get_sdk_tasks()],
                key=lambda x: x.id,
            ),
        )

    def create_plan_iterator(self, execution_plan):
        check.inst(execution_plan, ExecutionPlan)

        instance = DagsterInstance.ephemeral()
        instance.get_or_create_run(
            pipeline_name=execution_plan.pipeline_def.display_name,
            run_id=execution_plan.pipeline_def.display_name,
            environment_dict=self.environment_dict,
        )

        plan_iterator = execute_plan_iterator(
            execution_plan,
            instance.get_run_by_id(execution_plan.pipeline_def.display_name),
            instance=instance,
            environment_dict=self.environment_dict,
        )

        return plan_iterator

    def get_flyte_sdk_workflow(self):
        execution_plan = create_execution_plan(
            self.pipeline, environment_dict=self.environment_dict
        )

        ordered_step_dict = execution_plan.execution_deps()
        for step_key in ordered_step_dict:
            current_node = self.get_sdk_node(execution_plan, step_key)
            self.sdk_node_dict[step_key.split('.')[0]] = current_node

    def get_sdk_node(self, execution_plan, step_key):
        plan_iterator = self.create_plan_iterator(execution_plan)

        def wrapper(wf_params):  # pylint: disable=unused-argument
            event = None
            while not event or event.event_type_value != "STEP_SUCCESS":
                event = next(plan_iterator)

        # flytekit uses this name for an internal representation, make it unique to the step key
        wrapper.__name__ = step_key.split('.')[0]
        return sdk_runnable.SdkRunnableTask(
            task_function=wrapper,
            task_type=constants.SdkTaskType.PYTHON_TASK,
            discovery_version='',
            retries=0,
            interruptible=False,
            deprecated='',
            storage_request=None,
            cpu_request=None,
            gpu_request=None,
            memory_request=None,
            storage_limit=None,
            cpu_limit=None,
            gpu_limit=None,
            memory_limit=None,
            discoverable=False,
            timeout=datetime.timedelta(seconds=0),
            environment=None,
            custom={},
        )

    def get_sdk_tasks(self):
        return self.sdk_node_dict.items()


def compile_pipeline_to_flyte(pipeline, environment_dict=None, module=__name__):
    check.inst(pipeline, PipelineDefinition)
    check.inst(environment_dict, dict)

    flyte_compiler = DagsterFlyteCompiler(pipeline, environment_dict=environment_dict)
    return flyte_compiler(module=module)
