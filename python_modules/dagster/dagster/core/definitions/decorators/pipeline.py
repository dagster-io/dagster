from functools import update_wrapper

from dagster import check

from ..composition import enter_composition, exit_composition
from ..hook import HookDefinition
from ..mode import ModeDefinition
from ..pipeline import PipelineDefinition
from ..preset import PresetDefinition


class _Pipeline(object):
    def __init__(
        self,
        name=None,
        mode_defs=None,
        preset_defs=None,
        description=None,
        tags=None,
        hook_defs=None,
    ):
        self.name = check.opt_str_param(name, "name")
        self.mode_definitions = check.opt_list_param(mode_defs, "mode_defs", ModeDefinition)
        self.preset_definitions = check.opt_list_param(preset_defs, "preset_defs", PresetDefinition)
        self.description = check.opt_str_param(description, "description")
        self.tags = check.opt_dict_param(tags, "tags")
        self.hook_defs = check.opt_set_param(hook_defs, "hook_defs", of_type=HookDefinition)

    def __call__(self, fn):
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        enter_composition(self.name, "@pipeline")
        try:
            fn()
        finally:
            context = exit_composition()

        pipeline_def = PipelineDefinition(
            name=self.name,
            dependencies=context.dependencies,
            solid_defs=context.solid_defs,
            mode_defs=self.mode_definitions,
            preset_defs=self.preset_definitions,
            description=self.description,
            tags=self.tags,
            hook_defs=self.hook_defs,
        )
        update_wrapper(pipeline_def, fn)
        return pipeline_def


def pipeline(
    name=None, description=None, mode_defs=None, preset_defs=None, tags=None, hook_defs=None
):
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
    )
