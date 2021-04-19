import inspect
from functools import update_wrapper, wraps
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, Union

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.core.types.dagster_type import DagsterTypeKind
from dagster.seven import funcsigs

from ...decorator_utils import (
    positional_arg_name_list,
    split_function_parameters,
    validate_decorated_fn_positionals,
)
from ..events import AssetMaterialization, ExpectationResult, Materialization, Output
from ..inference import infer_input_props, infer_output_definitions
from ..input import InputDefinition
from ..output import OutputDefinition
from ..solid import SolidDefinition


class _Solid:
    def __init__(
        self,
        name: Optional[str] = None,
        input_defs: Optional[List[InputDefinition]] = None,
        output_defs: Optional[List[OutputDefinition]] = None,
        description: Optional[str] = None,
        required_resource_keys: Optional[Set[str]] = None,
        config_schema: Optional[Union[Any, Dict[str, Any]]] = None,
        tags: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
    ):
        self.name = check.opt_str_param(name, "name")
        self.input_defs = check.opt_list_param(input_defs, "input_defs", InputDefinition)
        self.output_defs = check.opt_nullable_list_param(
            output_defs, "output_defs", OutputDefinition
        )

        self.description = check.opt_str_param(description, "description")

        # these will be checked within SolidDefinition
        self.required_resource_keys = required_resource_keys
        self.tags = tags
        self.version = version

        # config will be checked within SolidDefinition
        self.config_schema = config_schema

    def __call__(self, fn: Callable[..., Any]) -> SolidDefinition:
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        output_defs = (
            self.output_defs
            if self.output_defs is not None
            else infer_output_definitions("@solid", self.name, fn)
        )

        resolved_input_defs, positional_inputs = resolve_checked_solid_fn_inputs(
            decorator_name="@solid",
            fn_name=self.name,
            compute_fn=fn,
            explicit_input_defs=self.input_defs,
            has_context_arg=True,
            exclude_nothing=True,
        )
        compute_fn = _create_solid_compute_wrapper(fn, resolved_input_defs, output_defs)

        solid_def = SolidDefinition(
            name=self.name,
            input_defs=resolved_input_defs,
            output_defs=output_defs,
            compute_fn=compute_fn,
            config_schema=self.config_schema,
            description=self.description or fn.__doc__,
            required_resource_keys=self.required_resource_keys,
            tags=self.tags,
            positional_inputs=positional_inputs,
            version=self.version,
        )
        update_wrapper(solid_def, fn)
        return solid_def


def solid(
    name: Union[Callable[..., Any], Optional[str]] = None,
    description: Optional[str] = None,
    input_defs: Optional[List[InputDefinition]] = None,
    output_defs: Optional[List[OutputDefinition]] = None,
    config_schema: Optional[Union[Any, Dict[str, Any]]] = None,
    required_resource_keys: Optional[Set[str]] = None,
    tags: Optional[Dict[str, Any]] = None,
    version: Optional[str] = None,
) -> Union[_Solid, SolidDefinition]:
    """Create a solid with the specified parameters from the decorated function.

    This shortcut simplifies the core :class:`SolidDefinition` API by exploding arguments into
    kwargs of the decorated compute function and omitting additional parameters when they are not
    needed.

    Input and output definitions will be inferred from the type signature of the decorated function
    if not explicitly provided.

    The decorated function will be used as the solid's compute function. The signature of the
    decorated function is more flexible than that of the ``compute_fn`` in the core API; it may:

    1. Return a value. This value will be wrapped in an :py:class:`Output` and yielded by the compute function.
    2. Return an :py:class:`Output`. This output will be yielded by the compute function.
    3. Yield :py:class:`Output` or other :ref:`event objects <events>`. Same as default compute behavior.

    Note that options 1) and 2) are incompatible with yielding other events -- if you would like
    to decorate a function that yields events, it must also wrap its eventual output in an
    :py:class:`Output` and yield it.

    @solid supports ``async def`` functions as well, including async generators when yielding multiple
    events or outputs. Note that async solids will generally be run on their own unless using a custom
    :py:class:`Executor` implementation that supports running them together.

    Args:
        name (Optional[str]): Name of solid. Must be unique within any :py:class:`PipelineDefinition`
            using the solid.
        description (Optional[str]): Human-readable description of this solid. If not provided, and
            the decorated function has docstring, that docstring will be used as the description.
        input_defs (Optional[List[InputDefinition]]):
            Information about the inputs to the solid. Information provided here will be combined
            with what can be inferred from the function signature, with these explicit InputDefinitions
            taking precedence.
        output_defs (Optional[List[OutputDefinition]]):
            List of output definitions. Inferred from typehints if not provided.
        config_schema (Optional[ConfigSchema): The schema for the config. If set, Dagster will check
            that config provided for the solid matches this schema and fail if it does not. If not
            set, Dagster will accept any config provided for the solid.
        required_resource_keys (Optional[Set[str]]): Set of resource handles required by this solid.
        tags (Optional[Dict[str, Any]]): Arbitrary metadata for the solid. Frameworks may
            expect and require certain metadata to be attached to a solid. Users should generally
            not set metadata directly. Values that are not strings will be json encoded and must meet
            the criteria that `json.loads(json.dumps(value)) == value`.
        version (Optional[str]): (Experimental) The version of the solid's compute_fn. Two solids should have
            the same version if and only if they deterministically produce the same outputs when
            provided the same inputs.


    Examples:

        .. code-block:: python

            @solid
            def hello_world(_context):
                print('hello')

            @solid
            def hello_world(_context):
                return {'foo': 'bar'}

            @solid
            def hello_world(_context):
                return Output(value={'foo': 'bar'})

            @solid
            def hello_world(_context):
                yield Output(value={'foo': 'bar'})

            @solid
            def hello_world(_context, foo):
                return foo

            @solid(
                input_defs=[InputDefinition(name="foo", str)],
                output_defs=[OutputDefinition(str)]
            )
            def hello_world(_context, foo):
                # explicitly type and name inputs and outputs
                return foo

            @solid
            def hello_world(_context, foo: str) -> str:
                # same as above inferred from signature
                return foo

            @solid
            def hello_world(context, foo):
                context.log.info('log something')
                return foo

            @solid(
                config_schema={'str_value' : Field(str)}
            )
            def hello_world(context, foo):
                # context.solid_config is a dictionary with 'str_value' key
                return foo + context.solid_config['str_value']

    """
    # This case is for when decorator is used bare, without arguments. e.g. @solid versus @solid()
    if callable(name):
        check.invariant(input_defs is None)
        check.invariant(output_defs is None)
        check.invariant(description is None)
        check.invariant(config_schema is None)
        check.invariant(required_resource_keys is None)
        check.invariant(tags is None)
        check.invariant(version is None)

        return _Solid()(name)

    return _Solid(
        name=name,
        input_defs=input_defs,
        output_defs=output_defs,
        config_schema=config_schema,
        description=description,
        required_resource_keys=required_resource_keys,
        tags=tags,
        version=version,
    )


def _coerce_solid_output_to_iterator(result, context, output_defs):
    if isinstance(result, (AssetMaterialization, Materialization, ExpectationResult)):
        raise DagsterInvariantViolationError(
            (
                "Error in solid {solid_name}: If you are returning an AssetMaterialization "
                "or an ExpectationResult from solid you must yield them to avoid "
                "ambiguity with an implied result from returning a value.".format(
                    solid_name=context.solid.name
                )
            )
        )

    if isinstance(result, Output):
        yield result
    elif len(output_defs) == 1:
        if result is None and output_defs[0].is_required is False:
            context.log.warn(
                'Value "None" returned for non-required output "{output_name}". '
                "This value will be passed to downstream solids. For conditional execution use\n"
                '  yield Output(value, "{output_name}")\n'
                "when you want the downstream solids to execute, "
                "and do not yield it when you want downstream solids to skip.".format(
                    output_name=output_defs[0].name
                )
            )
        yield Output(value=result, output_name=output_defs[0].name)
    elif result is not None:
        if not output_defs:
            raise DagsterInvariantViolationError(
                (
                    "Error in solid {solid_name}: Unexpectedly returned output {result} "
                    "of type {type_}. Solid is explicitly defined to return no "
                    "results."
                ).format(solid_name=context.solid.name, result=result, type_=type(result))
            )

        raise DagsterInvariantViolationError(
            (
                "Error in solid {solid_name}: Solid unexpectedly returned "
                "output {result} of type {type_}. Should "
                "be a generator, containing or yielding "
                "{n_results} results: {{{expected_results}}}."
            ).format(
                solid_name=context.solid.name,
                result=result,
                type_=type(result),
                n_results=len(output_defs),
                expected_results=", ".join(
                    [
                        "'{result_name}': {dagster_type}".format(
                            result_name=output_def.name,
                            dagster_type=output_def.dagster_type,
                        )
                        for output_def in output_defs
                    ]
                ),
            )
        )


async def _coerce_async_solid_to_async_gen(awaitable, context, output_defs):
    result = await awaitable
    for event in _coerce_solid_output_to_iterator(result, context, output_defs):
        yield event


def _create_solid_compute_wrapper(
    fn: Callable, input_defs: List[InputDefinition], output_defs: List[OutputDefinition]
):
    check.callable_param(fn, "fn")
    check.list_param(input_defs, "input_defs", of_type=InputDefinition)
    check.list_param(output_defs, "output_defs", of_type=OutputDefinition)

    input_names = [
        input_def.name
        for input_def in input_defs
        if not input_def.dagster_type.kind == DagsterTypeKind.NOTHING
    ]

    @wraps(fn)
    def compute(context, input_defs) -> Generator[Output, None, None]:
        kwargs = {}
        for input_name in input_names:
            kwargs[input_name] = input_defs[input_name]

        result = fn(context, **kwargs)

        if inspect.isgenerator(result):
            return result
        elif inspect.isasyncgen(result):
            return result
        elif inspect.iscoroutine(result):
            return _coerce_async_solid_to_async_gen(result, context, output_defs)
        else:
            return _coerce_solid_output_to_iterator(result, context, output_defs)

    return compute


def resolve_checked_solid_fn_inputs(
    decorator_name: str,
    fn_name: str,
    compute_fn: Callable[..., Any],
    explicit_input_defs: List[InputDefinition],
    has_context_arg: bool,
    exclude_nothing: bool,  # should Nothing type inputs be excluded from compute_fn args
) -> Tuple[List[InputDefinition], List[str]]:
    """
    Validate provided input definitions and infer the remaining from the type signature of the compute_fn
    Returns the resolved set of InputDefinitions and the positions of input names (which is used
    during graph composition).
    """
    expected_positionals = ["context"] if has_context_arg else []

    if exclude_nothing:
        explicit_names = set(
            inp.name
            for inp in explicit_input_defs
            if not inp.dagster_type.kind == DagsterTypeKind.NOTHING
        )
        nothing_names = set(
            inp.name
            for inp in explicit_input_defs
            if inp.dagster_type.kind == DagsterTypeKind.NOTHING
        )
    else:
        explicit_names = set(inp.name for inp in explicit_input_defs)
        nothing_names = set()

    # Currently being super strict about naming. Might be a good idea to relax. Starting strict.
    fn_positionals, input_args = split_function_parameters(compute_fn, expected_positionals)

    # Validate Positional Parameters
    missing_positional = validate_decorated_fn_positionals(fn_positionals, expected_positionals)
    if missing_positional:
        raise DagsterInvalidDefinitionError(
            "{decorator_name} '{solid_name}' decorated function does not have required positional "
            "parameter '{missing_param}'. Solid functions should only have keyword arguments "
            "that match input names and a first positional parameter named 'context'.".format(
                decorator_name=decorator_name, solid_name=fn_name, missing_param=missing_positional
            )
        )

    # Validate non positional parameters
    used_inputs = set()
    inputs_to_infer = set()
    has_kwargs = False

    for param in input_args:
        if param.kind == funcsigs.Parameter.VAR_KEYWORD:
            has_kwargs = True
        elif param.kind == funcsigs.Parameter.VAR_POSITIONAL:
            raise DagsterInvalidDefinitionError(
                f"{decorator_name} '{fn_name}' decorated function has positional vararg parameter "
                f"'{param}'. Solid functions should only have keyword arguments that match "
                "input names and a first positional parameter named 'context'."
            )

        else:
            if param.name not in explicit_names:
                if param.name in nothing_names:
                    raise DagsterInvalidDefinitionError(
                        f"{decorator_name} '{fn_name}' decorated function has parameter '{param.name}' that is "
                        "one of the solid input_defs of type 'Nothing' which should not be included since "
                        "no data will be passed for it. "
                    )
                else:
                    inputs_to_infer.add(param.name)

            else:
                used_inputs.add(param.name)

    undeclared_inputs = explicit_names - used_inputs
    if not has_kwargs and undeclared_inputs:
        undeclared_inputs_printed = ", '".join(undeclared_inputs)
        raise DagsterInvalidDefinitionError(
            f"{decorator_name} '{fn_name}' decorated function does not have parameter(s) "
            f"'{undeclared_inputs_printed}', which are in solid's input_defs. Solid functions "
            "should only have keyword arguments that match input names and a first positional "
            "parameter named 'context'."
        )

    inferred_props = {
        inferred.name: inferred
        for inferred in infer_input_props(decorator_name, fn_name, compute_fn, has_context_arg)
    }
    input_defs = []
    for input_def in explicit_input_defs:
        if input_def.name in inferred_props:
            # combine any information missing on the explicit def that can be inferred
            input_defs.append(input_def.combine_with_inferred(inferred_props[input_def.name]))
        else:
            # pass through those that don't have any inference info, such as Nothing type inputs
            input_defs.append(input_def)

    # build defs from the inferred props for those without explicit entries
    input_defs.extend(
        InputDefinition.create_from_inferred(inferred)
        for inferred in inferred_props.values()
        if inferred.name in inputs_to_infer
    )

    return input_defs, positional_arg_name_list(input_args)
