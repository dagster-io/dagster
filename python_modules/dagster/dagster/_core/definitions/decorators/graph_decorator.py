from collections.abc import Mapping, Sequence
from functools import update_wrapper
from typing import Any, Callable, Optional, Union, overload

import dagster._check as check
from dagster._core.decorator_utils import format_docstring_for_description
from dagster._core.definitions.config import ConfigMapping
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.input import GraphIn, InputDefinition
from dagster._core.definitions.output import GraphOut, OutputDefinition


class _Graph:
    name: Optional[str]
    description: Optional[str]
    input_defs: Sequence[InputDefinition]
    output_defs: Optional[Sequence[OutputDefinition]]
    ins: Optional[Mapping[str, GraphIn]]
    out: Optional[Union[GraphOut, Mapping[str, GraphOut]]]
    tags: Optional[Mapping[str, str]]
    config_mapping: Optional[ConfigMapping]

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        input_defs: Optional[Sequence[InputDefinition]] = None,
        output_defs: Optional[Sequence[OutputDefinition]] = None,
        ins: Optional[Mapping[str, GraphIn]] = None,
        out: Optional[Union[GraphOut, Mapping[str, GraphOut]]] = None,
        tags: Optional[Mapping[str, Any]] = None,
        config_mapping: Optional[ConfigMapping] = None,
    ):
        self.name = check.opt_str_param(name, "name")
        self.description = check.opt_str_param(description, "description")
        self.input_defs = check.opt_sequence_param(
            input_defs, "input_defs", of_type=InputDefinition
        )
        self.did_pass_outputs = output_defs is not None or out is not None
        self.output_defs = check.opt_nullable_sequence_param(
            output_defs, "output_defs", of_type=OutputDefinition
        )
        self.ins = ins
        self.out = out
        self.tags = tags
        self.config_mapping = check.opt_inst_param(config_mapping, "config_mapping", ConfigMapping)

    def __call__(self, fn: Callable[..., Any]) -> GraphDefinition:
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        if self.ins is not None:
            input_defs = [inp.to_definition(name) for name, inp in self.ins.items()]
        else:
            input_defs = check.opt_list_param(
                self.input_defs, "input_defs", of_type=InputDefinition
            )

        if self.out is None:
            output_defs = self.output_defs
        elif isinstance(self.out, GraphOut):
            output_defs = [self.out.to_definition(name=None)]
        else:
            check.dict_param(self.out, "out", key_type=str, value_type=GraphOut)
            output_defs = [out.to_definition(name=name) for name, out in self.out.items()]

        from dagster._core.definitions.composition import do_composition

        (
            input_mappings,
            output_mappings,
            dependencies,
            node_defs,
            config_mapping,
            positional_inputs,
            input_assets,
        ) = do_composition(
            decorator_name="@graph",
            graph_name=self.name,
            fn=fn,
            provided_input_defs=input_defs,
            provided_output_defs=output_defs,
            ignore_output_from_composition_fn=False,
            config_mapping=self.config_mapping,
        )

        graph_def = GraphDefinition(
            name=self.name,
            dependencies=dependencies,
            node_defs=node_defs,
            description=self.description or format_docstring_for_description(fn),
            input_mappings=input_mappings,
            output_mappings=output_mappings,
            config=config_mapping,
            positional_inputs=positional_inputs,
            tags=self.tags,
            input_assets=input_assets,
            composition_fn=fn,
        )
        update_wrapper(graph_def, fn)
        return graph_def


@overload
def graph(compose_fn: Callable[..., Any]) -> GraphDefinition: ...


@overload
def graph(
    *,
    name: Optional[str] = ...,
    description: Optional[str] = ...,
    input_defs: Optional[Sequence[InputDefinition]] = ...,
    output_defs: Optional[Sequence[OutputDefinition]] = ...,
    ins: Optional[Mapping[str, GraphIn]] = ...,
    out: Optional[Union[GraphOut, Mapping[str, GraphOut]]] = ...,
    tags: Optional[Mapping[str, Any]] = ...,
    config: Optional[Union[ConfigMapping, Mapping[str, Any]]] = ...,
) -> _Graph: ...


def graph(
    compose_fn: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    input_defs: Optional[Sequence[InputDefinition]] = None,
    output_defs: Optional[Sequence[OutputDefinition]] = None,
    ins: Optional[Mapping[str, GraphIn]] = None,
    out: Optional[Union[GraphOut, Mapping[str, GraphOut]]] = None,
    tags: Optional[Mapping[str, Any]] = None,
    config: Optional[Union[ConfigMapping, Mapping[str, Any]]] = None,
) -> Union[GraphDefinition, _Graph]:
    """Create an op graph with the specified parameters from the decorated composition function.

    Using this decorator allows you to build up a dependency graph by writing a
    function that invokes ops (or other graphs) and passes the output to subsequent invocations.

    Args:
        name (Optional[str]):
            The name of the op graph. Must be unique within any :py:class:`RepositoryDefinition` containing the graph.
        description (Optional[str]):
            A human-readable description of the graph.
        input_defs (Optional[List[InputDefinition]]):
            Information about the inputs that this graph maps. Information provided here
            will be combined with what can be inferred from the function signature, with these
            explicit InputDefinitions taking precedence.

            Uses of inputs in the body of the decorated composition function will determine
            the :py:class:`InputMappings <InputMapping>` passed to the underlying
            :py:class:`GraphDefinition`.
        output_defs (Optional[List[OutputDefinition]]):
            Output definitions for the graph. If not provided explicitly, these will be inferred from typehints.

            Uses of these outputs in the body of the decorated composition function, as well as the
            return value of the decorated function, will be used to infer the appropriate set of
            :py:class:`OutputMappings <OutputMapping>` for the underlying
            :py:class:`GraphDefinition`.

            To map multiple outputs, return a dictionary from the composition function.
        ins (Optional[Dict[str, GraphIn]]):
            Information about the inputs that this graph maps. Information provided here
            will be combined with what can be inferred from the function signature, with these
            explicit GraphIn taking precedence.
        out (Optional[Union[GraphOut, Dict[str, GraphOut]]]):
            Information about the outputs that this graph maps. Information provided here will be
            combined with what can be inferred from the return type signature if the function does
            not use yield.

            To map multiple outputs, return a dictionary from the composition function.
       tags (Optional[Dict[str, Any]]): Arbitrary metadata for any execution run of the graph.
            Values that are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.  These tag values may be overwritten by tag
            values provided at invocation time.

       config (Optional[Union[ConfigMapping], Mapping[str, Any]):
            Describes how the graph is configured at runtime.

            If a :py:class:`ConfigMapping` object is provided, then the graph takes on the config
            schema of this object. The mapping will be applied at runtime to generate the config for
            the graph's constituent nodes.

            If a dictionary is provided, then it will be used as the default run config for the
            graph. This means it must conform to the config schema of the underlying nodes. Note
            that the values provided will be viewable and editable in the Dagster UI, so be careful
            with secrets. its constituent nodes.

            If no value is provided, then the config schema for the graph is the default (derived
            from the underlying nodes).
    """
    if compose_fn is not None:
        check.invariant(description is None)
        return _Graph()(compose_fn)

    config_mapping = None
    # Case 1: a dictionary of config is provided, convert to config mapping.
    if config is not None and not isinstance(config, ConfigMapping):
        config = check.dict_param(config, "config", key_type=str)
        config_mapping = ConfigMapping(config_fn=lambda _: config, config_schema=None)
    # Case 2: actual config mapping is provided.
    else:
        config_mapping = config

    return _Graph(
        name=name,
        description=description,
        input_defs=input_defs,
        output_defs=output_defs,
        ins=ins,
        out=out,
        tags=tags,
        config_mapping=config_mapping,
    )
