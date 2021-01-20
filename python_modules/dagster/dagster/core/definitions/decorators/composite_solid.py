from functools import update_wrapper
from typing import Any, Callable, Dict, List, Optional, Union

from dagster import check
from dagster.core.definitions.definition_config_schema import (
    convert_user_facing_definition_config_schema,
)

from ..composition import do_composition
from ..input import InputDefinition
from ..output import OutputDefinition
from ..solid import CompositeSolidDefinition


class _CompositeSolid:
    def __init__(
        self,
        name: Optional[str] = None,
        input_defs: Optional[List[InputDefinition]] = None,
        output_defs: Optional[List[OutputDefinition]] = None,
        description: Optional[str] = None,
        config_schema: Any = None,
        config_fn: Optional[Callable[[dict], dict]] = None,
    ):
        self.name = check.opt_str_param(name, "name")
        self.input_defs = check.opt_nullable_list_param(input_defs, "input_defs", InputDefinition)
        self.output_defs = check.opt_nullable_list_param(output_defs, "output", OutputDefinition)
        self.description = check.opt_str_param(description, "description")

        self.config_schema = convert_user_facing_definition_config_schema(config_schema)
        self.config_fn = check.opt_callable_param(config_fn, "config_fn")

    def __call__(self, fn: Callable[..., Any]):
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

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
            self.config_schema,
            self.config_fn,
            ignore_output_from_composition_fn=False,
        )

        composite_def = CompositeSolidDefinition(
            name=self.name,
            input_mappings=input_mappings,
            output_mappings=output_mappings,
            dependencies=dependencies,
            solid_defs=solid_defs,
            description=self.description,
            config_mapping=config_mapping,
            positional_inputs=positional_inputs,
        )
        update_wrapper(composite_def, fn)
        return composite_def


def composite_solid(
    name: Union[Optional[str], Callable[..., Any]] = None,
    input_defs: Optional[List[InputDefinition]] = None,
    output_defs: Optional[List[OutputDefinition]] = None,
    description: Optional[str] = None,
    config_schema: Optional[Dict[str, Any]] = None,
    config_fn: Optional[Callable[[dict], dict]] = None,
) -> _CompositeSolid:
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
        input_defs (Optional[List[InputDefinition]]): Input definitions for the composite solid.
            If not provided explicitly, these will be inferred from typehints.

            Uses of these inputs in the body of the decorated composition function will be used to
            infer the appropriate set of :py:class:`InputMappings <InputMapping>` passed to the
            underlying :py:class:`CompositeSolidDefinition`.
        output_defs (Optional[List[OutputDefinition]]): Output definitions for the composite solid.
            If not provided explicitly, these will be inferred from typehints.

            Uses of these outputs in the body of the decorated composition function, as well as the
            return value of the decorated function, will be used to infer the appropriate set of
            :py:class:`OutputMappings <OutputMapping>` for the underlying
            :py:class:`CompositeSolidDefinition`.

            To map multiple outputs, return a dictionary from the composition function.
        config_schema (Optional[ConfigSchema]): The schema for the config. Must be combined with the
            `config_fn` argument in order to transform this config into the config for the contained
            solids.
        config_fn (Callable[[dict], dict]): By specifying a config mapping
            function, you can override the configuration for the child solids contained within this
            composite solid.

            Config mappings require the configuration field to be specified as ``config_schema``, which
            will be exposed as the configuration field for the composite solid, as well as a
            configuration mapping function, ``config_fn``, which maps the config provided to the
            composite solid to the config that will be provided to the child solids.

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
