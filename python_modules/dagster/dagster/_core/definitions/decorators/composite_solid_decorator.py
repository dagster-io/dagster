from functools import update_wrapper
from typing import Any, Callable, List, Optional, Union, overload

import dagster._check as check
from dagster._config import UserConfigSchema
from dagster._core.decorator_utils import format_docstring_for_description

from ..composition import do_composition, get_validated_config_mapping
from ..input import InputDefinition
from ..output import OutputDefinition
from ..solid_definition import CompositeSolidDefinition


class _CompositeSolid:
    def __init__(
        self,
        name: Optional[str] = None,
        input_defs: Optional[List[InputDefinition]] = None,
        output_defs: Optional[List[OutputDefinition]] = None,
        description: Optional[str] = None,
        config_schema: Optional[UserConfigSchema] = None,
        config_fn: Optional[Callable[[dict], dict]] = None,
    ):
        self.name = check.opt_str_param(name, "name")
        self.input_defs = check.opt_list_param(input_defs, "input_defs", InputDefinition)
        self.output_defs = check.opt_nullable_list_param(output_defs, "output", OutputDefinition)
        self.description = check.opt_str_param(description, "description")

        self.config_schema = config_schema  # gets validated in do_composition
        self.config_fn = check.opt_callable_param(config_fn, "config_fn")

    def __call__(self, fn: Callable[..., Any]):
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        config_mapping = get_validated_config_mapping(
            self.name, self.config_schema, self.config_fn, decorator_name="composite_solid"
        )

        (
            input_mappings,
            output_mappings,
            dependencies,
            solid_defs,
            config_mapping,
            positional_inputs,
        ) = do_composition(
            "@composite_solid",
            self.name,
            fn,
            self.input_defs,
            self.output_defs,
            config_mapping,
            ignore_output_from_composition_fn=False,
        )

        composite_def = CompositeSolidDefinition(
            name=self.name,
            input_mappings=input_mappings,
            output_mappings=output_mappings,
            dependencies=dependencies,
            solid_defs=solid_defs,
            description=self.description or format_docstring_for_description(fn),
            config_mapping=config_mapping,
            positional_inputs=positional_inputs,
        )
        update_wrapper(composite_def, fn)
        return composite_def


@overload
def composite_solid(
    name: Callable[..., Any],
) -> CompositeSolidDefinition:
    ...


@overload
def composite_solid(
    name: Optional[str] = ...,
    input_defs: Optional[List[InputDefinition]] = ...,
    output_defs: Optional[List[OutputDefinition]] = ...,
    description: Optional[str] = ...,
    config_schema: Optional[UserConfigSchema] = ...,
    config_fn: Optional[Callable[[dict], dict]] = ...,
) -> _CompositeSolid:
    ...


def composite_solid(
    name: Optional[Union[Callable[..., Any], str]] = None,
    input_defs: Optional[List[InputDefinition]] = None,
    output_defs: Optional[List[OutputDefinition]] = None,
    description: Optional[str] = None,
    config_schema: Optional[UserConfigSchema] = None,
    config_fn: Optional[Callable[[dict], dict]] = None,
) -> Union[CompositeSolidDefinition, _CompositeSolid]:
    """Create a composite solid with the specified parameters from the decorated composition
    function.

    Using this decorator allows you to build up the dependency graph of the composite by writing a
    function that invokes solids and passes the output to other solids. This is similar to the use
    of the :py:func:`@pipeline <pipeline>` decorator, with the additional ability to remap inputs,
    outputs, and config across the composite boundary.

    Args:
        name (Optional[str]): Name for the new composite solid. Must be unique within any
            :py:class:`PipelineDefinition` using the solid.
        description (Optional[str]): Human-readable description of the new composite solid.
        input_defs (Optional[List[InputDefinition]]):
            Information about the inputs that this composite solid maps. Information provided here
            will be combined with what can be inferred from the function signature, with these
            explicit InputDefinitions taking precedence.

            Uses of inputs in the body of the decorated composition function will determine
            the :py:class:`InputMappings <InputMapping>` passed to the underlying
            :py:class:`CompositeSolidDefinition`.
        output_defs (Optional[List[OutputDefinition]]):
            Information about the outputs this composite solid maps. Information provided here
            will be combined with what can be inferred from the return type signature if there
            is only one OutputDefinition.

            Uses of these outputs in the body of the decorated composition function, as well as the
            return value of the decorated function, will be used to infer the appropriate set of
            :py:class:`OutputMappings <OutputMapping>` for the underlying
            :py:class:`CompositeSolidDefinition`.

            To map multiple outputs, return a dictionary from the composition function.
        config_schema (Optional[ConfigSchema]): If the `config_fn` argument is provided, this
            argument can be provided to set the schema for outer config that is passed to the
            `config_fn`. If `config_fn` is provided, but this argument is not provided, any config
            will be accepted.
        config_fn (Callable[[dict], dict]): By specifying a config mapping
            function, you can override the configuration for the child solids contained within this
            composite solid.  ``config_fn``, maps the config provided to the
            composite solid to the config that will be provided to the child solids.

            If this argument is provided, the `config_schema` argument can also be provided to limit
            what config values can be passed to the composite solid.

    Examples:

        .. code-block:: python

            @lambda_solid
            def add_one(num: int) -> int:
                return num + 1

            @composite_solid
            def add_two(num: int) -> int:
                adder_1 = add_one.alias('adder_1')
                adder_2 = add_one.alias('adder_2')

                return adder_2(adder_1(num))

    """
    if callable(name):
        check.invariant(input_defs is None)
        check.invariant(output_defs is None)
        check.invariant(description is None)
        check.invariant(config_schema is None)
        check.invariant(config_fn is None)
        return _CompositeSolid()(name)

    return _CompositeSolid(
        name=name,
        input_defs=input_defs,
        output_defs=output_defs,
        description=description,
        config_schema=config_schema,
        config_fn=config_fn,
    )
