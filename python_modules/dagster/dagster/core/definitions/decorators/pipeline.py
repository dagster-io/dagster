from functools import update_wrapper
from typing import Any, Callable, Dict, List, Optional, Set, Union

from dagster import check
from dagster.utils.backcompat import experimental_arg_warning

from ..hook import HookDefinition
from ..input import InputDefinition
from ..mode import ModeDefinition
from ..output import OutputDefinition
from ..pipeline import PipelineDefinition
from ..preset import PresetDefinition


class _Pipeline:
    def __init__(
        self,
        name: Optional[str] = None,
        mode_defs: Optional[List[ModeDefinition]] = None,
        preset_defs: Optional[List[PresetDefinition]] = None,
        description: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        hook_defs: Optional[Set[HookDefinition]] = None,
        input_defs: Optional[List[InputDefinition]] = None,
        output_defs: Optional[List[OutputDefinition]] = None,
        config_schema: Optional[Dict[str, Any]] = None,
        config_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ):
        self.name = check.opt_str_param(name, "name")
        self.mode_definitions = check.opt_list_param(mode_defs, "mode_defs", ModeDefinition)
        self.preset_definitions = check.opt_list_param(preset_defs, "preset_defs", PresetDefinition)
        self.description = check.opt_str_param(description, "description")
        self.tags = check.opt_dict_param(tags, "tags")
        self.hook_defs = check.opt_set_param(hook_defs, "hook_defs", of_type=HookDefinition)
        self.input_defs = check.opt_list_param(input_defs, "input_defs", of_type=InputDefinition)
        self.did_pass_outputs = output_defs is not None
        self.output_defs = check.opt_nullable_list_param(
            output_defs, "output_defs", of_type=OutputDefinition
        )
        self.config_schema = config_schema
        self.config_fn = check.opt_callable_param(config_fn, "config_fn")

    def __call__(self, fn: Callable[..., Any]) -> PipelineDefinition:
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        from dagster.core.definitions.decorators.composite_solid import do_composition

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
            self.config_schema,
            self.config_fn,
            ignore_output_from_composition_fn=not self.did_pass_outputs,
        )

        pipeline_def = PipelineDefinition(
            name=self.name,
            dependencies=dependencies,
            solid_defs=solid_defs,
            mode_defs=self.mode_definitions,
            preset_defs=self.preset_definitions,
            description=self.description,
            tags=self.tags,
            hook_defs=self.hook_defs,
            input_mappings=input_mappings,
            output_mappings=output_mappings,
            config_mapping=config_mapping,
            positional_inputs=positional_inputs,
        )
        update_wrapper(pipeline_def, fn)
        return pipeline_def


def pipeline(
    name: Union[Callable[..., Any], Optional[str]] = None,
    description: Optional[str] = None,
    mode_defs: Optional[List[ModeDefinition]] = None,
    preset_defs: Optional[List[PresetDefinition]] = None,
    tags: Optional[Dict[str, Any]] = None,
    hook_defs: Optional[Set[HookDefinition]] = None,
    input_defs: Optional[List[InputDefinition]] = None,
    output_defs: Optional[List[OutputDefinition]] = None,
    config_schema: Optional[Dict[str, Any]] = None,
    config_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
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
    )
