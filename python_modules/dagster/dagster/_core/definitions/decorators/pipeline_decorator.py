from functools import update_wrapper
from typing import Any, Callable, Mapping, Optional, Sequence, Set, Union, overload

import dagster._check as check
from dagster._config import UserConfigSchema
from dagster._core.decorator_utils import format_docstring_for_description
from dagster._core.definitions.policy import RetryPolicy
from dagster._utils.backcompat import experimental_arg_warning

from ..graph_definition import GraphDefinition
from ..hook_definition import HookDefinition
from ..input import InputDefinition
from ..mode import ModeDefinition
from ..output import OutputDefinition
from ..pipeline_definition import PipelineDefinition
from ..preset import PresetDefinition
from ..version_strategy import VersionStrategy


class _Pipeline:
    def __init__(
        self,
        name: Optional[str] = None,
        mode_defs: Optional[Sequence[ModeDefinition]] = None,
        preset_defs: Optional[Sequence[PresetDefinition]] = None,
        description: Optional[str] = None,
        tags: Optional[Mapping[str, Any]] = None,
        hook_defs: Optional[Set[HookDefinition]] = None,
        input_defs: Optional[Sequence[InputDefinition]] = None,
        output_defs: Optional[Sequence[OutputDefinition]] = None,
        config_schema: Optional[UserConfigSchema] = None,
        config_fn: Optional[Callable[[Mapping[str, Any]], Mapping[str, Any]]] = None,
        solid_retry_policy: Optional[RetryPolicy] = None,
        version_strategy: Optional[VersionStrategy] = None,
    ):
        self.name = check.opt_str_param(name, "name")
        self.mode_definitions = check.opt_sequence_param(mode_defs, "mode_defs", ModeDefinition)
        self.preset_definitions = check.opt_sequence_param(
            preset_defs, "preset_defs", PresetDefinition
        )
        self.description = check.opt_str_param(description, "description")
        self.tags = check.opt_mapping_param(tags, "tags")
        self.hook_defs = check.opt_set_param(hook_defs, "hook_defs", of_type=HookDefinition)
        self.input_defs = check.opt_sequence_param(
            input_defs, "input_defs", of_type=InputDefinition
        )
        self.did_pass_outputs = output_defs is not None
        self.output_defs = check.opt_nullable_sequence_param(
            output_defs, "output_defs", of_type=OutputDefinition
        )
        self.config_schema = config_schema
        self.config_fn = check.opt_callable_param(config_fn, "config_fn")
        self.solid_retry_policy = check.opt_inst_param(
            solid_retry_policy, "solid_retry_policy", RetryPolicy
        )
        self.version_strategy = check.opt_inst_param(
            version_strategy, "version_strategy", VersionStrategy
        )

    def __call__(self, fn: Callable[..., Any]) -> PipelineDefinition:
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        from ..composition import do_composition, get_validated_config_mapping

        config_mapping = get_validated_config_mapping(
            self.name, self.config_schema, self.config_fn, decorator_name="pipeline"
        )

        (
            input_mappings,
            output_mappings,
            dependencies,
            solid_defs,
            config_mapping,
            positional_inputs,
        ) = do_composition(
            "@pipeline",
            self.name,
            fn,
            self.input_defs,
            self.output_defs,
            config_mapping,
            ignore_output_from_composition_fn=not self.did_pass_outputs,
        )

        pipeline_def = PipelineDefinition(
            mode_defs=self.mode_definitions,
            preset_defs=self.preset_definitions,
            graph_def=GraphDefinition(
                name=self.name,
                description=None,  # put desc on the pipeline
                dependencies=dependencies,
                node_defs=solid_defs,
                input_mappings=input_mappings,
                output_mappings=output_mappings,
                config=config_mapping,
                positional_inputs=positional_inputs,
            ),
            tags=self.tags,
            description=self.description or format_docstring_for_description(fn),
            hook_defs=self.hook_defs,
            solid_retry_policy=self.solid_retry_policy,
            version_strategy=self.version_strategy,
        )
        update_wrapper(pipeline_def, fn)
        return pipeline_def


@overload
def pipeline(
    name: Callable[..., Any],
) -> PipelineDefinition:
    ...


@overload
def pipeline(
    name: Optional[str] = ...,
    description: Optional[str] = ...,
    mode_defs: Optional[Sequence[ModeDefinition]] = ...,
    preset_defs: Optional[Sequence[PresetDefinition]] = ...,
    tags: Optional[Mapping[str, Any]] = ...,
    hook_defs: Optional[Set[HookDefinition]] = ...,
    input_defs: Optional[Sequence[InputDefinition]] = ...,
    output_defs: Optional[Sequence[OutputDefinition]] = ...,
    config_schema: Optional[UserConfigSchema] = ...,
    config_fn: Optional[Callable[[Mapping[str, Any]], Mapping[str, Any]]] = ...,
    solid_retry_policy: Optional[RetryPolicy] = ...,
    version_strategy: Optional[VersionStrategy] = ...,
) -> _Pipeline:
    pass


def pipeline(
    name: Optional[Union[Callable[..., Any], str]] = None,
    description: Optional[str] = None,
    mode_defs: Optional[Sequence[ModeDefinition]] = None,
    preset_defs: Optional[Sequence[PresetDefinition]] = None,
    tags: Optional[Mapping[str, Any]] = None,
    hook_defs: Optional[Set[HookDefinition]] = None,
    input_defs: Optional[Sequence[InputDefinition]] = None,
    output_defs: Optional[Sequence[OutputDefinition]] = None,
    config_schema: Optional[UserConfigSchema] = None,
    config_fn: Optional[Callable[[Mapping[str, Any]], Mapping[str, Any]]] = None,
    solid_retry_policy: Optional[RetryPolicy] = None,
    version_strategy: Optional[VersionStrategy] = None,
) -> Union[PipelineDefinition, _Pipeline]:
    """Create a pipeline with the specified parameters from the decorated composition function.

    Using this decorator allows you to build up the dependency graph of the pipeline by writing a
    function that invokes solids and passes the output to other solids.

    Args:
        name (Optional[str]): The name of the pipeline. Must be unique within any
            :py:class:`RepositoryDefinition` containing the pipeline.
        description (Optional[str]): A human-readable description of the pipeline.
        mode_defs (Optional[List[ModeDefinition]]): The set of modes in which this pipeline can
            operate. Modes are used to attach resources, custom loggers, custom system storage
            options, and custom executors to a pipeline. Modes can be used, e.g., to vary
            available resource and logging implementations between local test and production runs.
        preset_defs (Optional[List[PresetDefinition]]): A set of preset collections of configuration
            options that may be used to execute a pipeline. A preset consists of an environment
            dict, an optional subset of solids to execute, and a mode selection. Presets can be used
            to ship common combinations of options to pipeline end users in Python code, and can
            be selected by tools like Dagit.
        tags (Optional[Dict[str, Any]]): Arbitrary metadata for any execution run of the pipeline.
            Values that are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.  These tag values may be overwritten by tag
            values provided at invocation time.
        hook_defs (Optional[Set[HookDefinition]]): A set of hook definitions applied to the
            pipeline. When a hook is applied to a pipeline, it will be attached to all solid
            instances within the pipeline.
        solid_retry_policy (Optional[RetryPolicy]): The default retry policy for all solids in
            this pipeline. Only used if retry policy is not defined on the solid definition or
            solid invocation.
        version_strategy (Optional[VersionStrategy]): The version strategy to use with this
            pipeline. Providing a VersionStrategy will enable memoization on the pipeline.

    Example:
        .. code-block:: python

            @solid(output_defs=[OutputDefinition(int, "two"), OutputDefinition(int, "four")])
            def emit_two_four(_) -> int:
                yield Output(2, "two")
                yield Output(4, "four")


            @lambda_solid
            def add_one(num: int) -> int:
                return num + 1


            @lambda_solid
            def mult_two(num: int) -> int:
                return num * 2


            @pipeline
            def math_pipeline():
                two, four = emit_two_four()
                add_one(two)
                mult_two(four)
    """
    if input_defs is not None:
        experimental_arg_warning("input_defs", "pipeline")

    if output_defs is not None:
        experimental_arg_warning("output_defs", "pipeline")

    if config_schema is not None:
        experimental_arg_warning("config_schema", "pipeline")

    if config_fn is not None:
        experimental_arg_warning("config_fn", "pipeline")

    if callable(name):
        check.invariant(description is None)
        return _Pipeline()(name)

    return _Pipeline(
        name=name,
        mode_defs=mode_defs,
        preset_defs=preset_defs,
        description=description,
        tags=tags,
        hook_defs=hook_defs,
        input_defs=input_defs,
        output_defs=output_defs,
        config_schema=config_schema,
        config_fn=config_fn,
        solid_retry_policy=solid_retry_policy,
        version_strategy=version_strategy,
    )
