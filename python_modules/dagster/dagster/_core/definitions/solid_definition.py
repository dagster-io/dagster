from typing import Any, Iterator, Mapping, Optional, Sequence, Union

from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.types.dagster_type import DagsterType

from .config import ConfigMapping
from .definition_config_schema import IDefinitionConfigSchema
from .dependency import IDependencyDefinition, NodeInvocation
from .graph_definition import GraphDefinition
from .input import InputMapping
from .node_definition import NodeDefinition
from .output import OutputMapping


class CompositeSolidDefinition(GraphDefinition):
    """The core unit of composition and abstraction, composite solids allow you to
    define a solid from a graph of solids.

    In the same way you would refactor a block of code in to a function to deduplicate, organize,
    or manage complexity - you can refactor solids in a pipeline in to a composite solid.

    Args:
        name (str): The name of this composite solid. Must be unique within any
            :py:class:`PipelineDefinition` using the solid.
        solid_defs (List[Union[SolidDefinition, CompositeSolidDefinition]]): The set of solid
            definitions used in this composite solid. Composites may be arbitrarily nested.
        input_mappings (Optional[List[InputMapping]]): Define the inputs to the composite solid,
            and how they map to the inputs of its constituent solids.
        output_mappings (Optional[List[OutputMapping]]): Define the outputs of the composite solid,
            and how they map from the outputs of its constituent solids.
        config_mapping (Optional[ConfigMapping]): By specifying a config mapping, you can override
            the configuration for the child solids contained within this composite solid. Config
            mappings require both a configuration field to be specified, which is exposed as the
            configuration for the composite solid, and a configuration mapping function, which
            is called to map the configuration of the composite solid into the configuration that
            is applied to any child solids.
        dependencies (Optional[Mapping[Union[str, NodeInvocation], Mapping[str, DependencyDefinition]]]):
            A structure that declares where each solid gets its inputs. The keys at the top
            level dict are either string names of solids or NodeInvocations. The values
            are dicts that map input names to DependencyDefinitions.
        description (Optional[str]): Human readable description of this composite solid.
        tags (Optional[Mapping[str, Any]]): Arbitrary metadata for the solid. Frameworks may
            expect and require certain metadata to be attached to a solid. Users should generally
            not set metadata directly. Values that are not strings will be json encoded and must meet
            the criteria that `json.loads(json.dumps(value)) == value`.
            may expect and require certain metadata to be attached to a solid.
        positional_inputs (Optional[List[str]]): The positional order of the inputs if it
            differs from the order of the input mappings

    Examples:

        .. code-block:: python

            @lambda_solid
            def add_one(num: int) -> int:
                return num + 1

            add_two = CompositeSolidDefinition(
                'add_two',
                solid_defs=[add_one],
                dependencies={
                    NodeInvocation('add_one', 'adder_1'): {},
                    NodeInvocation('add_one', 'adder_2'): {'num': DependencyDefinition('adder_1')},
                },
                input_mappings=[InputDefinition('num', Int).mapping_to('adder_1', 'num')],
                output_mappings=[OutputDefinition(Int).mapping_from('adder_2')],
            )
    """

    def __init__(
        self,
        name: str,
        solid_defs: Sequence[NodeDefinition],
        input_mappings: Optional[Sequence[InputMapping]] = None,
        output_mappings: Optional[Sequence[OutputMapping]] = None,
        config_mapping: Optional[ConfigMapping] = None,
        dependencies: Optional[
            Mapping[Union[str, NodeInvocation], Mapping[str, IDependencyDefinition]]
        ] = None,
        description: Optional[str] = None,
        tags: Optional[Mapping[str, str]] = None,
        positional_inputs: Optional[Sequence[str]] = None,
    ):

        super(CompositeSolidDefinition, self).__init__(
            name=name,
            description=description,
            node_defs=solid_defs,
            dependencies=dependencies,
            tags=tags,
            positional_inputs=positional_inputs,
            input_mappings=input_mappings,
            output_mappings=output_mappings,
            config=config_mapping,
        )

    def all_dagster_types(self) -> Iterator[DagsterType]:
        yield from self.all_input_output_types()

        for node_def in self._node_defs:
            yield from node_def.all_dagster_types()

    def copy_for_configured(
        self,
        name: str,
        description: Optional[str],
        config_schema: IDefinitionConfigSchema,
        config_or_config_fn: Any,
    ) -> "CompositeSolidDefinition":
        config_mapping = self._config_mapping
        if config_mapping is None:
            raise DagsterInvalidDefinitionError(
                "Only composite solids utilizing config mapping can be pre-configured. The "
                'composite solid "{graph_name}" does not have a config mapping, and thus has '
                "nothing to be configured.".format(graph_name=self.name)
            )

        return CompositeSolidDefinition(
            name=name,
            solid_defs=self._node_defs,
            input_mappings=self.input_mappings,
            output_mappings=self.output_mappings,
            config_mapping=ConfigMapping(
                config_mapping.config_fn,
                config_schema=config_schema,
                receive_processed_config_values=config_mapping.receive_processed_config_values,
            ),
            dependencies=self.dependencies,
            description=description or self.description,
            tags=self.tags,
            positional_inputs=self.positional_inputs,
        )

    @property
    def node_type_str(self) -> str:
        return "composite solid"

    @property
    def is_graph_job_op_node(self) -> bool:
        return False
