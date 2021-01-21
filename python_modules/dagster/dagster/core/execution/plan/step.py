from enum import Enum
from typing import TYPE_CHECKING, Dict, List, NamedTuple, Optional, Set, Union

from dagster import check
from dagster.core.definitions.utils import validate_tags
from dagster.serdes import whitelist_for_serdes
from dagster.utils import merge_dicts

from .handle import ResolvedFromDynamicStepHandle, StepHandle, UnresolvedStepHandle
from .inputs import StepInput, UnresolvedStepInput
from .outputs import StepOutput

if TYPE_CHECKING:
    from dagster.core.definitions.dependency import Solid, SolidHandle
    from dagster.core.definitions.hook import HookDefinition


@whitelist_for_serdes
class StepKind(Enum):
    COMPUTE = "COMPUTE"
    UNRESOLVED = "UNRESOLVED"


def is_executable_step(step: Union["ExecutionStep", "UnresolvedExecutionStep"]) -> bool:
    # This function is set up defensively to ensure new step types handled properly
    if isinstance(step, ExecutionStep):
        return True
    elif isinstance(step, UnresolvedExecutionStep):
        return False
    else:
        check.failed(f"Unexpected execution step type {step}")


class ExecutionStep(
    NamedTuple(
        "_ExecutionStep",
        [
            ("handle", Union[StepHandle, ResolvedFromDynamicStepHandle]),
            ("pipeline_name", str),
            ("step_input_dict", Dict[str, StepInput]),
            ("step_output_dict", Dict[str, StepOutput]),
            ("tags", Dict[str, str]),
            ("logging_tags", Dict[str, str]),
        ],
    )
):
    def __new__(
        cls,
        handle: Union[StepHandle, ResolvedFromDynamicStepHandle],
        pipeline_name: str,
        step_inputs: List[StepInput],
        step_outputs: List[StepOutput],
        tags: Optional[Dict[str, str]],
        logging_tags: Optional[Dict[str, str]] = None,
    ):
        return super(ExecutionStep, cls).__new__(
            cls,
            handle=check.inst_param(handle, "handle", (StepHandle, ResolvedFromDynamicStepHandle)),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            step_input_dict={
                si.name: si
                for si in check.list_param(step_inputs, "step_inputs", of_type=StepInput)
            },
            step_output_dict={
                so.name: so
                for so in check.list_param(step_outputs, "step_outputs", of_type=StepOutput)
            },
            tags=validate_tags(check.opt_dict_param(tags, "tags", key_type=str)),
            logging_tags=merge_dicts(
                {
                    "step_key": handle.to_key(),
                    "pipeline": pipeline_name,
                    "solid": handle.solid_handle.name,
                },
                check.opt_dict_param(logging_tags, "logging_tags"),
            ),
        )

    @property
    def solid_handle(self) -> "SolidHandle":
        return self.handle.solid_handle

    @property
    def key(self) -> str:
        return self.handle.to_key()

    @property
    def solid_name(self) -> str:
        return self.solid_handle.name

    @property
    def kind(self) -> StepKind:
        return StepKind.COMPUTE

    @property
    def step_outputs(self) -> List[StepOutput]:
        return list(self.step_output_dict.values())

    @property
    def step_inputs(self) -> List[StepInput]:
        return list(self.step_input_dict.values())

    def has_step_output(self, name: str) -> bool:
        check.str_param(name, "name")
        return name in self.step_output_dict

    def step_output_named(self, name: str) -> StepOutput:
        check.str_param(name, "name")
        return self.step_output_dict[name]

    def has_step_input(self, name: str) -> bool:
        check.str_param(name, "name")
        return name in self.step_input_dict

    def step_input_named(self, name: str) -> StepInput:
        check.str_param(name, "name")
        return self.step_input_dict[name]

    def get_execution_dependency_keys(self) -> Set[str]:
        deps = set()
        for inp in self.step_inputs:
            deps.update(inp.dependency_keys)
        return deps

    def get_mapping_key(self):
        if isinstance(self.handle, ResolvedFromDynamicStepHandle):
            return self.handle.mapping_key

        return None


class UnresolvedExecutionStep(
    NamedTuple(
        "_UnresolvedExecutionStep",
        [
            ("handle", UnresolvedStepHandle),
            ("pipeline_name", str),
            ("step_input_dict", Dict[str, Union[StepInput, UnresolvedStepInput]]),
            ("step_output_dict", Dict[str, StepOutput]),
            ("tags", Dict[str, str]),
        ],
    )
):
    def __new__(
        cls,
        handle: UnresolvedStepHandle,
        pipeline_name: str,
        step_inputs: List[Union[StepInput, UnresolvedStepInput]],
        step_outputs: List[StepOutput],
        tags: Optional[Dict[str, str]],
    ):
        return super(UnresolvedExecutionStep, cls).__new__(
            cls,
            handle=check.inst_param(handle, "handle", UnresolvedStepHandle),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            step_input_dict={
                si.name: si
                for si in check.list_param(
                    step_inputs, "step_inputs", of_type=(StepInput, UnresolvedStepInput)
                )
            },
            step_output_dict={
                so.name: so
                for so in check.list_param(step_outputs, "step_outputs", of_type=StepOutput)
            },
            tags=check.opt_dict_param(tags, "tags", key_type=str),
        )

    @property
    def solid_handle(self) -> "SolidHandle":
        return self.handle.solid_handle

    @property
    def key(self) -> str:
        return self.handle.to_key()

    @property
    def kind(self) -> StepKind:
        return StepKind.UNRESOLVED

    @property
    def step_outputs(self) -> List[StepOutput]:
        return list(self.step_output_dict.values())

    @property
    def step_inputs(self) -> List[Union[StepInput, UnresolvedStepInput]]:
        return list(self.step_input_dict.values())

    def step_output_named(self, name: str) -> StepOutput:
        check.str_param(name, "name")
        return self.step_output_dict[name]

    def get_all_dependency_keys(self) -> Set[str]:
        deps = set()
        for inp in self.step_inputs:
            if isinstance(inp, StepInput):
                deps.update(
                    [handle.step_key for handle in inp.get_step_output_handle_dependencies()]
                )
            elif isinstance(inp, UnresolvedStepInput):
                deps.update(
                    [
                        handle.step_key
                        for handle in inp.get_step_output_handle_deps_with_placeholders()
                    ]
                )
            else:
                check.failed(f"Unexpected step input type {inp}")

        return deps

    @property
    def resolved_by_step_key(self) -> str:
        keys = set()
        for inp in self.step_inputs:
            if isinstance(inp, UnresolvedStepInput):
                keys.add(inp.resolved_by_step_key)

        check.invariant(len(keys) == 1, "Unresolved step expects one and only one dynamic step key")

        return list(keys)[0]

    @property
    def resolved_by_output_name(self) -> str:
        keys = set()
        for inp in self.step_inputs:
            if isinstance(inp, UnresolvedStepInput):
                keys.add(inp.resolved_by_output_name)

        check.invariant(
            len(keys) == 1, "Unresolved step expects one and only one dynamic output name"
        )

        return list(keys)[0]

    def resolve(
        self, resolved_by_step_key: str, mappings: Dict[str, List[str]]
    ) -> List[ExecutionStep]:
        check.invariant(
            self.resolved_by_step_key == resolved_by_step_key,
            "resolving dynamic output step key did not match",
        )

        execution_steps = []

        for output_name, mapped_keys in mappings.items():
            if self.resolved_by_output_name != output_name:
                continue

            for mapped_key in mapped_keys:
                # handle output_name alignment
                resolved_inputs = [_resolved_input(inp, mapped_key) for inp in self.step_inputs]

                execution_steps.append(
                    ExecutionStep(
                        handle=ResolvedFromDynamicStepHandle(self.handle.solid_handle, mapped_key),
                        pipeline_name=self.pipeline_name,
                        step_inputs=resolved_inputs,
                        step_outputs=self.step_outputs,
                        tags=self.tags,
                    )
                )

        return execution_steps


def _resolved_input(step_input: Union[StepInput, UnresolvedStepInput], map_key: str):
    if isinstance(step_input, StepInput):
        return step_input
    return step_input.resolve(map_key)
