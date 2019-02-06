from collections import defaultdict
from dagster import check


from dagster.core.execution_context import ExecutionMetadata
from dagster.core.execution_plan.create import create_execution_plan_core
from dagster.core.execution_plan.objects import (
    ExecutionPlanInfo,
    ExecutionSelection,
    SolidOutputHandle,
    StepOutputHandle,
)
from dagster.core.execution_plan.simple_engine import execute_plan_core
from dagster.core.execution_plan.utility import create_value_thunk_step

from .dependency import DependencyDefinition

from .input import InputDefinition

from .output import OutputDefinition

from .result import Result

from .solid import ISolidDefinition

from .utils import check_valid_name, check_opt_two_dim_dict

from .pipeline_creation import create_execution_structure


def two_dim_dict_values(ddict):
    if ddict:
        for inner_dict in ddict.values():
            for value in inner_dict.values():
                yield value


def _create_value_thunk_fn(composite_input_value):
    return lambda _info, plan_builder, solid, input_def: create_value_thunk_step(
        plan_builder,
        solid,
        input_def.runtime_type,
        step_key='solid.{solid_name}.input.{input_name}.value'.format(
            solid_name=solid.name, input_name=input_def.name
        ),
        value=composite_input_value,
    )


class CompositeSolidDefinition(ISolidDefinition):
    def __init__(
        self,
        name,
        solid_defs,
        dependencies=None,
        input_mapping=None,
        output_mapping=None,
        description=None,
    ):
        self.name = check_valid_name(name)
        self.description = check.opt_str_param(description, 'description')
        check.list_param(solid_defs, 'solids')
        self.dependencies = check_opt_two_dim_dict(
            dependencies, 'dependencies', value_type=DependencyDefinition
        )

        self.input_mapping = check_opt_two_dim_dict(
            input_mapping, 'input_mapping', value_type=InputDefinition
        )
        self.output_mapping = check_opt_two_dim_dict(
            output_mapping, 'output_mapping', value_type=OutputDefinition
        )

        self.reverse_input_mapping = {}

        for inner_solid_name, inner_input_dict in self.input_mapping.items():
            for inner_input_name, input_def in inner_input_dict.items():
                self.reverse_input_mapping[input_def.name] = (inner_solid_name, inner_input_name)

        self.dependency_structure, self._solid_dict = create_execution_structure(
            solid_defs, self.dependencies
        )

        self.solids = list(self._solid_dict.values())

        self._input_dict = {inp.name: inp for inp in two_dim_dict_values(input_mapping)}
        self._output_dict = {out.name: out for out in two_dim_dict_values(output_mapping)}

        self.input_defs = list(self._input_dict.values())
        self.output_defs = list(self._output_dict.values())
        self.config_field = None  # TODO? right thing?

    def transform_fn(self, info, inputs):
        execution_plan = create_execution_plan_core(
            ExecutionPlanInfo(
                info.context,
                ExecutionSelection.from_composite_solid(info.pipeline_def, self),
                info.typed_environment,
                self.create_input_thunk_fns(inputs),
            ),
            ExecutionMetadata(
                info.context.run_id,
                info.context.get_tags(),
                info.context.event_callback,
                info.context.loggers,
            ),
        )

        results = list(execute_plan_core(info.context, execution_plan, throw_on_user_error=False))

        # TODO:
        # need to handle failure
        # execute_plan_core (or some wrapper) should return a dictionary indexed by StepOutputHandle

        step_result_dict = {}

        for result in results:
            if result.success:
                step_result_dict[
                    StepOutputHandle(result.step, result.success_data.output_name)
                ] = result

        for solid_result in self.gather_results(execution_plan, step_result_dict):
            yield solid_result

    def gather_results(self, execution_plan, step_result_dict):
        for solid_name, output_dict in self.output_mapping.items():
            for output_name, composite_output_def in output_dict.items():
                solid = self._solid_dict[solid_name]
                output_def = solid.output_def_named(output_name)
                solid_output_handle = SolidOutputHandle(self._solid_dict[solid_name], output_def)
                step_output = execution_plan.step_output_map[solid_output_handle]
                if step_output in step_result_dict:
                    yield Result(
                        step_result_dict[step_output].success_data.value, composite_output_def.name
                    )

                else:
                    check.failed('likely failed execution')

    def create_input_thunk_fns(self, inputs):
        thunk_fns = defaultdict(dict)

        # this should probably be created during the execution plan construction process
        # and then actually executed in the transform of that execution step
        for composite_input_name, composite_input_value in inputs.items():
            inner_solid_name, inner_input_name = self.reverse_input_mapping[composite_input_name]
            thunk_fns[inner_solid_name][inner_input_name] = _create_value_thunk_fn(
                composite_input_value
            )
        return thunk_fns

    def has_input(self, name):
        check.str_param(name, 'name')
        return name in self._input_dict

    def input_def_named(self, name):
        check.str_param(name, 'name')
        return self._input_dict[name]

    def has_output(self, name):
        check.str_param(name, 'name')
        return name in self._output_dict

    def output_def_named(self, name):
        check.str_param(name, 'name')
        return self._output_dict[name]

    def solid_named(self, name):
        return self._solid_dict[name]
