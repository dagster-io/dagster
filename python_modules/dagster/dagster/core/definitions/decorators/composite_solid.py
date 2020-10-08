from functools import update_wrapper

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError

from ..composition import (
    InputMappingNode,
    composite_mapping_from_output,
    enter_composition,
    exit_composition,
)
from ..config import ConfigMapping
from ..inference import (
    has_explicit_return_type,
    infer_input_definitions_for_composite_solid,
    infer_output_definitions,
)
from ..input import InputDefinition
from ..output import OutputDefinition
from ..solid import CompositeSolidDefinition
from .solid import validate_solid_fn


class _CompositeSolid(object):
    def __init__(
        self,
        name=None,
        input_defs=None,
        output_defs=None,
        description=None,
        config_schema=None,
        config_fn=None,
    ):
        self.name = check.opt_str_param(name, "name")
        self.input_defs = check.opt_nullable_list_param(input_defs, "input_defs", InputDefinition)
        self.output_defs = check.opt_nullable_list_param(output_defs, "output", OutputDefinition)
        self.description = check.opt_str_param(description, "description")

        check.opt_dict_param(
            config_schema, "config_schema"
        )  # don't want to assign dict below if config is None
        self.config_schema = config_schema
        self.config_fn = check.opt_callable_param(config_fn, "config_fn")

    def __call__(self, fn):
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        input_defs = (
            self.input_defs
            if self.input_defs is not None
            else infer_input_definitions_for_composite_solid(self.name, fn)
        )

        explicit_outputs = False
        if self.output_defs is not None:
            explicit_outputs = True
            output_defs = self.output_defs
        else:
            explicit_outputs = has_explicit_return_type(fn)
            output_defs = infer_output_definitions("@composite_solid", self.name, fn)

        positional_inputs = validate_solid_fn(
            "@composite_solid", self.name, fn, input_defs, exclude_nothing=False
        )

        kwargs = {input_def.name: InputMappingNode(input_def) for input_def in input_defs}

        output = None
        mapping = None
        enter_composition(self.name, "@composite_solid")
        try:
            output = fn(**kwargs)
            mapping = composite_mapping_from_output(output, output_defs, self.name)
        finally:
            context = exit_composition(mapping)

        check.invariant(
            context.name == self.name,
            "Composition context stack desync: received context for "
            '"{context.name}" expected "{self.name}"'.format(context=context, self=self),
        )

        # line up mappings in definition order
        input_mappings = []
        for defn in input_defs:
            mappings = [
                mapping
                for mapping in context.input_mappings
                if mapping.definition.name == defn.name
            ]

            if len(mappings) == 0:
                raise DagsterInvalidDefinitionError(
                    "@composite_solid '{solid_name}' has unmapped input '{input_name}'. "
                    "Remove it or pass it to the appropriate solid invocation.".format(
                        solid_name=self.name, input_name=defn.name
                    )
                )

            input_mappings += mappings

        output_mappings = []
        for defn in output_defs:
            mapping = context.output_mapping_dict.get(defn.name)
            if mapping is None:
                # if we inferred output_defs we will be flexible and either take a mapping or not
                if not explicit_outputs:
                    continue

                raise DagsterInvalidDefinitionError(
                    "@composite_solid '{solid_name}' has unmapped output '{output_name}'. "
                    "Remove it or return a value from the appropriate solid invocation.".format(
                        solid_name=self.name, output_name=defn.name
                    )
                )
            output_mappings.append(mapping)

        config_mapping = _get_validated_config_mapping(
            self.name, self.config_schema, self.config_fn
        )

        composite_def = CompositeSolidDefinition(
            name=self.name,
            input_mappings=input_mappings,
            output_mappings=output_mappings,
            dependencies=context.dependencies,
            solid_defs=context.solid_defs,
            description=self.description,
            config_mapping=config_mapping,
            positional_inputs=positional_inputs,
        )
        update_wrapper(composite_def, fn)
        return composite_def


def _get_validated_config_mapping(name, config_schema, config_fn):
    """Config mapping must set composite config_schema and config_fn or neither.
    """

    if config_fn is None and config_schema is None:
        return None
    elif config_fn is not None and config_schema is not None:
        return ConfigMapping(config_fn=config_fn, config_schema=config_schema)
    else:
        if config_fn is not None:
            raise DagsterInvalidDefinitionError(
                "@composite_solid '{solid_name}' defines a configuration function {config_fn} "
                "but does not define a configuration schema. If you intend this composite to take "
                "no config_schema, you must explicitly specify config_schema={{}}.".format(
                    solid_name=name, config_fn=config_fn.__name__
                )
            )
        else:
            raise DagsterInvalidDefinitionError(
                "@composite_solid '{solid_name}' defines a configuration schema but does not "
                "define a configuration function.".format(solid_name=name)
            )


def composite_solid(
    name=None,
    input_defs=None,
    output_defs=None,
    description=None,
    config_schema=None,
    config_fn=None,
):
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
