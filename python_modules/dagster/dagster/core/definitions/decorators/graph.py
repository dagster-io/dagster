from functools import update_wrapper

from dagster import check

from ..graph import GraphDefinition
from ..input import InputDefinition
from ..output import OutputDefinition


class _Graph:
    def __init__(
        self,
        name=None,
        description=None,
        input_defs=None,
        output_defs=None,
    ):
        self.name = check.opt_str_param(name, "name")
        self.description = check.opt_str_param(description, "description")
        self.input_defs = check.opt_nullable_list_param(
            input_defs, "input_defs", of_type=InputDefinition
        )
        self.did_pass_outputs = output_defs is not None
        self.output_defs = check.opt_nullable_list_param(
            output_defs, "output_defs", of_type=OutputDefinition
        )

    def __call__(self, fn):
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
            decorator_name="@graph",
            graph_name=self.name,
            fn=fn,
            provided_input_defs=self.input_defs,
            provided_output_defs=self.output_defs,
            ignore_output_from_composition_fn=False,
            config_schema=None,
            config_fn=None,
        )

        graph_def = GraphDefinition(
            name=self.name,
            dependencies=dependencies,
            node_defs=solid_defs,
            description=self.description,
            input_mappings=input_mappings,
            output_mappings=output_mappings,
            config_mapping=config_mapping,
            positional_inputs=positional_inputs,
        )
        update_wrapper(graph_def, fn)
        return graph_def


def graph(
    name=None,
    description=None,
    input_defs=None,
    output_defs=None,
):
    """Create a graph with the specified parameters from the decorated composition function.

    Using this decorator allows you to build up a dependency graph by writing a
    function that invokes solids (or other graphs) and passes the output to subsequent invocations.

    Args:
        name (Optional[str]):
            The name of the graph. Must be unique within any :py:class:`RepositoryDefinition` containing the graph.
        description (Optional[str]):
            A human-readable description of the graph.
        input_defs (Optional[List[InputDefinition]]):
            Input definitions for the graph.
            If not provided explicitly, these will be inferred from typehints.

            Uses of these inputs in the body of the decorated composition function will be used to
            infer the appropriate set of :py:class:`InputMappings <InputMapping>` passed to the
            underlying :py:class:`GraphDefinition`.
        output_defs (Optional[List[OutputDefinition]]):
            Output definitions for the graph. If not provided explicitly, these will be inferred from typehints.

            Uses of these outputs in the body of the decorated composition function, as well as the
            return value of the decorated function, will be used to infer the appropriate set of
            :py:class:`OutputMappings <OutputMapping>` for the underlying
            :py:class:`GraphDefinition`.

            To map multiple outputs, return a dictionary from the composition function.
    """
    if callable(name):
        check.invariant(description is None)
        return _Graph()(name)

    return _Graph(
        name=name,
        description=description,
        input_defs=input_defs,
        output_defs=output_defs,
    )
