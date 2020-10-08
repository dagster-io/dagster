import datetime
import sys
from collections import OrderedDict, defaultdict

import forge
from flytekit.common import constants
from flytekit.common.tasks import sdk_runnable
from flytekit.common.workflow import SdkWorkflow
from flytekit.sdk.tasks import inputs, outputs
from flytekit.sdk.types import Types
from flytekit.sdk.workflow import Input, Output

import dagster.core.types.dagster_type as types
from dagster import DagsterEventType, PipelineDefinition, check
from dagster.core.execution.api import (
    PlanExecutionContextManager,
    create_execution_plan,
    execute_plan,
)
from dagster.core.execution.context.system import SystemExecutionContext
from dagster.core.execution.plan.objects import ExecutionStep, StepOutputHandle
from dagster.core.execution.retries import Retries
from dagster.core.instance import DagsterInstance
from dagster.core.snap.execution_plan_snapshot import snapshot_from_execution_plan

# TODO: Schema
FLYTE_TYPES = {
    types.Int.key: Types.Integer,
    types.String.key: Types.String,
    types.Bool.key: Types.Boolean,
    types.Float.key: Types.Float,
}


class DagsterFlyteCompiler:
    def __init__(self, pipeline, run_config, compute_dict):
        check.inst(pipeline, PipelineDefinition)
        check.inst(run_config, dict)

        self.pipeline = pipeline
        self.run_config = run_config
        self.compute_dict = defaultdict(dict, compute_dict) if compute_dict else defaultdict(dict)
        self.execution_plan = None
        self.sdk_node_dict = OrderedDict()
        self.inputs = defaultdict(dict)
        self.outputs = defaultdict(dict)
        self.source_handles = defaultdict(dict)

    def __call__(self, module="__main__"):
        """
        Creates an SdkWorkflow from a dagster pipeline. Then, adds the nodes as attrs within the module
        that this function is invoked from. User will need to manually provide the module name.
        This is required because flytekit runs dir() on the module that the resultant container
        registers, in order  to discover the DAG structure.
        """

        self.execution_plan = create_execution_plan(self.pipeline, run_config=self.run_config)

        self.build_flyte_sdk_workflow()
        nodes = {}
        for name, node in self.get_sdk_tasks():
            setattr(sys.modules[module], name, node)
            nodes[name] = node(
                **self.inputs[name], **self.source_handle_inputs(name, nodes)
            ).assign_id_and_return(name)

        _inputs = [
            _input.rename_and_return_reference(name)
            for key in self.inputs.keys()
            for name, _input in self.inputs[key].items()
        ]

        # currently, we create an Output for every solid's output. A user may only want outputs for
        # solids at the highest topological level or for solids whose output is not used elsewhere.
        # However they may want to persist outputs from other levels as well.
        # Therefore, it may be simplest to create an Output for every Solid's output
        _outputs = [
            Output(
                getattr(nodes[key].outputs, name), sdk_type=flyte_type
            ).rename_and_return_reference("{}_{}".format(key, name))
            for key in self.outputs.keys()
            for name, flyte_type in self.outputs[key].items()
        ]

        return SdkWorkflow(
            inputs=sorted(_inputs, key=lambda x: x.name),
            outputs=sorted(_outputs, key=lambda x: x.name),
            nodes=sorted(nodes.values(), key=lambda x: x.id),
        )

    def build_flyte_sdk_workflow(self):
        ordered_step_dict = self.execution_plan.execution_deps()
        instance = DagsterInstance.ephemeral()
        pipeline_run = instance.create_run(
            pipeline_name=self.execution_plan.pipeline_def.display_name,
            run_id=self.execution_plan.pipeline_def.display_name,
            run_config=self.run_config,
            mode=None,
            solids_to_execute=None,
            step_keys_to_execute=None,
            status=None,
            tags=None,
            root_run_id=None,
            parent_run_id=None,
            pipeline_snapshot=self.execution_plan.pipeline_def.get_pipeline_snapshot(),
            execution_plan_snapshot=snapshot_from_execution_plan(
                self.execution_plan, self.execution_plan.pipeline_def.get_pipeline_snapshot_id()
            ),
            parent_pipeline_snapshot=self.execution_plan.pipeline_def.get_parent_pipeline_snapshot(),
        )

        initialization_manager = PlanExecutionContextManager(
            Retries.disabled_mode(),
            self.execution_plan,
            self.run_config,
            instance.get_run_by_id(self.execution_plan.pipeline_def.display_name),
            instance,
        )

        list(initialization_manager.prepare_context())
        pipeline_context = initialization_manager.get_context()

        for step_key in ordered_step_dict:
            solid_name = self.execution_plan.get_step_by_key(step_key).solid_name
            self.sdk_node_dict[solid_name] = self.get_sdk_node(
                pipeline_context,
                instance,
                pipeline_run,
                step_key,
                storage_request=self.compute_dict[solid_name].get("storage_request", None),
                cpu_request=self.compute_dict[solid_name].get("cpu_request", None),
                memory_request=self.compute_dict[solid_name].get("memory_request", None),
                storage_limit=self.compute_dict[solid_name].get("storage_limit", None),
                cpu_limit=self.compute_dict[solid_name].get("cpu_limit", None),
                memory_limit=self.compute_dict[solid_name].get("memory_limit", None),
            )

    def get_sdk_node(
        self,
        pipeline_context,
        instance,
        pipeline_run,
        step_key,
        task_type=constants.SdkTaskType.PYTHON_TASK,
        cache_version="",
        retries=0,
        interruptible=False,
        deprecated="",
        storage_request=None,
        cpu_request=None,
        gpu_request=None,
        memory_request=None,
        storage_limit=None,
        cpu_limit=None,
        gpu_limit=None,
        memory_limit=None,
        cache=False,
        timeout=datetime.timedelta(seconds=0),
        environment=None,
    ):
        execution_step = self.execution_plan.get_step_by_key(step_key)
        flyte_inputs = self.flyte_inputs(execution_step.step_input_dict, execution_step.solid_name)
        flyte_outputs = self.flyte_outputs(
            execution_step.step_output_dict, execution_step.solid_name
        )

        def wrapper(wf_params, *args, **kwargs):  # pylint: disable=unused-argument
            # TODO: We can't update config values via inputs from Flyte, because they are immutable
            plan = self.execution_plan.build_subset_plan([step_key])
            for param, arg in kwargs.items():
                self.inject_intermediates(pipeline_context, execution_step, param, arg)

            results = list(
                execute_plan(plan, instance, run_config=self.run_config, pipeline_run=pipeline_run,)
            )

            for result in results:
                step_context = pipeline_context.for_step(execution_step)
                self.output_value(step_context, step_key, result, execution_step, kwargs)

        # This will take the wrapper definition and re-create it with explicit parameters as keyword argumentss
        wrapper = forge.sign(
            forge.arg("wf_params"),
            *map(forge.arg, flyte_inputs.keys()),
            *map(forge.arg, flyte_outputs.keys())
        )(wrapper)

        # flytekit uses this name for an internal representation, make it unique to the step key
        wrapper.__name__ = execution_step.solid_name

        task = sdk_runnable.SdkRunnableTask(
            task_function=wrapper,
            task_type=task_type,
            discovery_version=cache_version,
            retries=retries,
            interruptible=interruptible,
            deprecated=deprecated,
            storage_request=storage_request,
            cpu_request=cpu_request,
            gpu_request=gpu_request,
            memory_request=memory_request,
            storage_limit=storage_limit,
            cpu_limit=cpu_limit,
            gpu_limit=gpu_limit,
            memory_limit=memory_limit,
            discoverable=cache,
            timeout=timeout,
            environment=environment,
            custom={},
        )

        if flyte_inputs:
            task = inputs(task, **flyte_inputs)
        if flyte_outputs:
            task = outputs(task, **flyte_outputs)

        return task

    def inject_intermediates(self, context, execution_step, key, value):
        check.inst(context, SystemExecutionContext)
        check.inst(execution_step, ExecutionStep)

        if (
            not execution_step.has_step_output(key)
            and execution_step.has_step_input(key)
            and execution_step.step_input_named(key).is_from_output
        ):

            step_input = execution_step.step_input_named(key)
            if step_input.is_from_single_output:
                output_handle = step_input.source_handles[0]
                step_context = context.for_step(
                    self.execution_plan.get_step_by_key(output_handle.step_key)
                )

                step_context.intermediate_storage.set_intermediate(
                    context=step_context,
                    dagster_type=step_input.dagster_type,
                    step_output_handle=output_handle,
                    value=value,
                )
            else:
                if not isinstance(value, list):
                    raise TypeError(
                        "input for {key} should be passed in as a list, because {key} originates from multiple outputs".format(
                            key=key
                        )
                    )
                if len(value) != len(step_input.source_handles):
                    raise ValueError(
                        "Expected argument to param: {} to be of length: {}, found {}".format(
                            key, len(step_input.source_handles), len(value)
                        )
                    )
                for val, output_handle in zip(value, step_input.source_handles):
                    step_context = context.for_step(
                        self.execution_plan.get_step_by_key(output_handle.step_key)
                    )

                    step_context.intermediate_storage.set_intermediate(
                        context=step_context,
                        dagster_type=step_input.dagster_type,
                        step_output_handle=output_handle,
                        value=val,
                    )

    def output_value(self, context, step_key, result, execution_step, kwargs):
        if (
            result.event_type == DagsterEventType.STEP_OUTPUT
            and result.step_key == step_key
            and result.step_output_data.output_name in execution_step.step_output_dict
            and result.step_output_data.output_name in kwargs
        ):
            dagster_type = execution_step.step_output_named(
                result.step_output_data.output_name
            ).dagster_type

            step_output_handle = StepOutputHandle.from_step(
                step=execution_step, output_name=result.step_output_data.output_name
            )

            if not context.intermediate_storage.has_intermediate(context, step_output_handle):
                # Not working for InMemoryIntermediateManager ?
                raise KeyError(
                    "No Intermediate Store record for StepOutput: {}".format(step_output_handle)
                )

            output_value = context.intermediate_storage.get_intermediate(
                context=context, dagster_type=dagster_type, step_output_handle=step_output_handle,
            ).obj

            kwargs[result.step_output_data.output_name].set(output_value)

    def flyte_inputs(self, step_inputs, solid_name):
        flyte_typed_inputs = self.map_dagster_types(step_inputs)
        for k, v in flyte_typed_inputs.items():
            step_input = step_inputs[k]
            if step_input.is_from_config:
                self.inputs[solid_name][k] = Input(
                    v, default=step_input.config_data.get("value", None)
                )
            elif step_input.is_from_output:
                self.source_handles[solid_name][k] = step_input.source_handles
            else:
                raise ValueError(
                    "StepInputSourceType of type DEFAULT_VALUE is not supported for use with Flyte at this time."
                )
        return flyte_typed_inputs

    def flyte_outputs(self, step_outputs, solid_name):
        flyte_typed_outputs = self.map_dagster_types(step_outputs)
        for k, v in flyte_typed_outputs.items():
            self.outputs[solid_name][k] = v

        return flyte_typed_outputs

    def map_dagster_types(self, step_types_dict):
        flyte_types = {}
        if any(map(lambda x: isinstance(x.dagster_type, types.Anyish), step_types_dict.values())):
            raise TypeError("Use of Dagster Type Any is forbidden for use with Flyte.")

        for k, v in step_types_dict.items():
            # ListType key/name is not reliable for our current mapping solution, can be improved
            try:
                if isinstance(v.dagster_type, types.ListType):
                    flyte_types[k] = [self.resolve_step_output_type(v)]
                    continue

                flyte_types[k] = FLYTE_TYPES[v.dagster_type.key]
            except KeyError:
                continue

        return flyte_types

    def get_sdk_tasks(self):
        return self.sdk_node_dict.items()

    def source_handle_inputs(self, name, nodes):
        def _get_output(_arg):
            if len(_arg) == 1:
                solid_name = self.execution_plan.get_step_by_key(_arg[0].step_key).solid_name
                return getattr(nodes[solid_name].outputs, _arg[0].output_name)
            return [_get_output([arg]) for arg in _arg]

        source_inputs = {
            param: _get_output(arg) for param, arg in self.source_handles[name].items()
        }

        return source_inputs

    def resolve_step_output_type(self, step_input_or_output):
        check.inst(step_input_or_output.dagster_type, types.ListType)
        if any(
            map(
                lambda x: isinstance(self.source_handle_type(x), types.Anyish),
                step_input_or_output.source_handles,
            )
        ):
            TypeError("Use of Dagster Type Any is forbidden for use with Flyte.")
        if any(
            [
                self.source_handle_type(source_handle)
                != self.source_handle_type(step_input_or_output.source_handles[0])
                for source_handle in step_input_or_output.source_handles
            ]
        ):
            raise TypeError(
                "In order to specify a List type in Flyte, all List elements must be of the same type."
            )
        dagster_type = self.source_handle_type(step_input_or_output.source_handles[0])
        flyte_type = FLYTE_TYPES[dagster_type.key]
        return flyte_type

    def source_handle_type(self, source_handle):
        return (
            self.execution_plan.get_step_by_key(source_handle.step_key)
            .step_output_named(source_handle.output_name)
            .dagster_type
        )


def compile_pipeline_to_flyte(pipeline, run_config, compute_dict=None, module=__name__):
    check.inst(pipeline, PipelineDefinition)
    check.inst(run_config, dict)

    flyte_compiler = DagsterFlyteCompiler(
        pipeline, run_config=run_config, compute_dict=compute_dict
    )

    return flyte_compiler(module=module)
