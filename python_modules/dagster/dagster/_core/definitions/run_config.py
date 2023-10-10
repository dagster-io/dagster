from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    Iterator,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from typing_extensions import TypeAlias

from dagster._config import (
    ALL_CONFIG_BUILTINS,
    ConfigType,
    Field,
    Permissive,
    Selector,
    Shape,
)
from dagster._config.pythonic_config import Config
from dagster._core.definitions.asset_layer import AssetLayer
from dagster._core.definitions.executor_definition import (
    ExecutorDefinition,
    execute_in_process_executor,
    in_process_executor,
)
from dagster._core.definitions.input import InputDefinition
from dagster._core.definitions.output import OutputDefinition
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.storage.input_manager import IInputManagerDefinition
from dagster._core.storage.output_manager import IOutputManagerDefinition
from dagster._core.types.dagster_type import ALL_RUNTIME_BUILTINS, construct_dagster_type_dictionary
from dagster._utils import check

from .configurable import ConfigurableDefinition
from .definition_config_schema import IDefinitionConfigSchema
from .dependency import DependencyStructure, GraphNode, Node, NodeHandle, NodeInput, OpNode
from .graph_definition import GraphDefinition
from .logger_definition import LoggerDefinition
from .op_definition import NodeDefinition, OpDefinition
from .resource_definition import ResourceDefinition

if TYPE_CHECKING:
    from .source_asset import SourceAsset


def define_resource_dictionary_cls(
    resource_defs: Mapping[str, ResourceDefinition],
    required_resources: AbstractSet[str],
) -> Shape:
    fields = {}
    for resource_name, resource_def in resource_defs.items():
        if resource_def.config_schema:
            is_required = None
            if resource_name not in required_resources:
                # explicitly make section not required if resource is not required
                # for the current mode
                is_required = False

            fields[resource_name] = def_config_field(
                resource_def,
                is_required=is_required,
                description=resource_def.description,
            )

    return Shape(fields=fields)


def remove_none_entries(ddict: Mapping[Any, Any]) -> dict:
    return {k: v for k, v in ddict.items() if v is not None}


def def_config_field(
    configurable_def: ConfigurableDefinition,
    is_required: Optional[bool] = None,
    description: Optional[str] = None,
) -> Field:
    return Field(
        Shape(
            {"config": configurable_def.config_field} if configurable_def.has_config_field else {}
        ),
        is_required=is_required,
        description=description,
    )


class RunConfigSchemaCreationData(NamedTuple):
    job_name: str
    nodes: Sequence[Node]
    graph_def: GraphDefinition
    dependency_structure: DependencyStructure
    executor_def: ExecutorDefinition
    resource_defs: Mapping[str, ResourceDefinition]
    logger_defs: Mapping[str, LoggerDefinition]
    ignored_nodes: Sequence[Node]
    required_resources: AbstractSet[str]
    direct_inputs: Mapping[str, Any]
    asset_layer: AssetLayer


def define_logger_dictionary_cls(creation_data: RunConfigSchemaCreationData) -> Shape:
    return Shape(
        {
            logger_name: def_config_field(logger_definition, is_required=False)
            for logger_name, logger_definition in creation_data.logger_defs.items()
        }
    )


def define_execution_field(executor_defs: Sequence[ExecutorDefinition], description: str) -> Field:
    default_in_process = False
    for executor_def in executor_defs:
        if executor_def == in_process_executor:
            default_in_process = True

    selector = selector_for_named_defs(executor_defs)

    if default_in_process:
        return Field(
            selector, default_value={in_process_executor.name: {}}, description=description
        )

    # If we are using the execute_in_process executor, then ignore all executor config.
    if len(executor_defs) == 1 and executor_defs[0] == execute_in_process_executor:
        return Field(Permissive(), is_required=False, default_value={}, description=description)

    return Field(selector, description=description)


def define_single_execution_field(executor_def: ExecutorDefinition, description: str) -> Field:
    return def_config_field(executor_def, description=description)


def define_run_config_schema_type(creation_data: RunConfigSchemaCreationData) -> ConfigType:
    execution_field = define_single_execution_field(
        creation_data.executor_def,
        "Configure how steps are executed within a run.",
    )

    top_level_node = GraphNode(
        name=creation_data.graph_def.name,
        definition=creation_data.graph_def,
        graph_definition=creation_data.graph_def,
    )

    fields = {
        "execution": execution_field,
        "loggers": Field(
            define_logger_dictionary_cls(creation_data),
            description="Configure how loggers emit messages within a run.",
        ),
        "resources": Field(
            define_resource_dictionary_cls(
                creation_data.resource_defs,
                creation_data.required_resources,
            ),
            description="Configure how shared resources are implemented within a run.",
        ),
        "inputs": get_inputs_field(
            node=top_level_node,
            handle=NodeHandle(top_level_node.name, parent=None),
            dependency_structure=creation_data.dependency_structure,
            resource_defs=creation_data.resource_defs,
            node_ignored=False,
            direct_inputs=creation_data.direct_inputs,
            input_source_assets={},
            asset_layer=creation_data.asset_layer,
        ),
    }

    if creation_data.graph_def.has_config_mapping:
        config_schema = cast(IDefinitionConfigSchema, creation_data.graph_def.config_schema)
        nodes_field = Field(
            {"config": config_schema.as_field()},
            description="Configure runtime parameters for ops or assets.",
        )
    else:
        nodes_field = Field(
            define_node_shape(
                nodes=creation_data.nodes,
                ignored_nodes=creation_data.ignored_nodes,
                dependency_structure=creation_data.dependency_structure,
                resource_defs=creation_data.resource_defs,
                asset_layer=creation_data.asset_layer,
                node_input_source_assets=creation_data.graph_def.node_input_source_assets,
            ),
            description="Configure runtime parameters for ops or assets.",
        )

    fields["ops"] = nodes_field

    return Shape(
        fields=remove_none_entries(fields),
    )


# Common pattern for a set of named definitions (e.g. executors)
# to build a selector so that one of them is selected
def selector_for_named_defs(named_defs) -> Selector:
    return Selector({named_def.name: def_config_field(named_def) for named_def in named_defs})


def get_inputs_field(
    node: Node,
    handle: NodeHandle,
    dependency_structure: DependencyStructure,
    resource_defs: Mapping[str, ResourceDefinition],
    node_ignored: bool,
    asset_layer: AssetLayer,
    input_source_assets: Mapping[str, "SourceAsset"],
    direct_inputs: Optional[Mapping[str, Any]] = None,
) -> Optional[Field]:
    direct_inputs = check.opt_mapping_param(direct_inputs, "direct_inputs")
    inputs_field_fields = {}
    for name, inp in node.definition.input_dict.items():
        inp_handle = NodeInput(node, inp)
        has_upstream = input_has_upstream(dependency_structure, inp_handle, node, name)
        if inp.input_manager_key:
            input_field = get_input_manager_input_field(node, inp, resource_defs)
        elif (
            # if you have asset definitions, input will be loaded from the source asset
            asset_layer.has_assets_defs
            or asset_layer.has_asset_check_defs
            and asset_layer.asset_key_for_input(handle, name)
            and not has_upstream
        ):
            input_field = None
        elif name in direct_inputs and not has_upstream:
            input_field = None
        elif name in input_source_assets and not has_upstream:
            input_field = None
        elif inp.dagster_type.loader and not has_upstream:
            input_field = get_type_loader_input_field(node, name, inp)
        else:
            input_field = None

        if input_field:
            inputs_field_fields[name] = input_field

    if not inputs_field_fields:
        return None
    if node_ignored:
        return Field(
            Shape(inputs_field_fields),
            is_required=False,
            description=(
                "This op is not present in the current op selection, "
                "the input config values are allowed but ignored."
            ),
        )
    else:
        return Field(Shape(inputs_field_fields))


def input_has_upstream(
    dependency_structure: DependencyStructure,
    input_handle: NodeInput,
    node: Node,
    input_name: str,
) -> bool:
    return dependency_structure.has_deps(input_handle) or node.container_maps_input(input_name)


def get_input_manager_input_field(
    node: Node,
    input_def: InputDefinition,
    resource_defs: Mapping[str, ResourceDefinition],
) -> Optional[Field]:
    if input_def.input_manager_key:
        if input_def.input_manager_key not in resource_defs:
            raise DagsterInvalidDefinitionError(
                f"Input '{input_def.name}' for {node.describe_node()} requires input_manager_key"
                f" '{input_def.input_manager_key}', but no resource has been provided. Please"
                " include a resource definition for that key in the provided resource_defs."
            )

        input_manager = resource_defs[input_def.input_manager_key]
        if not isinstance(input_manager, IInputManagerDefinition):
            raise DagsterInvalidDefinitionError(
                f"Input '{input_def.name}' for {node.describe_node()} requires input_manager_key "
                f"'{input_def.input_manager_key}', but the resource definition provided is not an "
                "IInputManagerDefinition"
            )

        input_config_schema = input_manager.input_config_schema
        if input_config_schema:
            return input_config_schema.as_field()
        return None

    return None


def get_type_loader_input_field(node: Node, input_name: str, input_def: InputDefinition) -> Field:
    loader = check.not_none(input_def.dagster_type.loader)
    return Field(
        loader.schema_type,
        is_required=(not node.definition.input_has_default(input_name)),
    )


def get_outputs_field(
    node: Node,
    resource_defs: Mapping[str, ResourceDefinition],
) -> Optional[Field]:
    output_manager_fields = {}
    for name, output_def in node.definition.output_dict.items():
        output_manager_output_field = get_output_manager_output_field(
            node, output_def, resource_defs
        )
        if output_manager_output_field:
            output_manager_fields[name] = output_manager_output_field

    return Field(Shape(output_manager_fields)) if output_manager_fields else None


def get_output_manager_output_field(
    node: Node, output_def: OutputDefinition, resource_defs: Mapping[str, ResourceDefinition]
) -> Optional[ConfigType]:
    if output_def.io_manager_key not in resource_defs:
        raise DagsterInvalidDefinitionError(
            f'Output "{output_def.name}" for {node.describe_node()} requires io_manager_key '
            f'"{output_def.io_manager_key}", but no resource has been provided. Please include a '
            "resource definition for that key in the provided resource_defs."
        )
    if not isinstance(resource_defs[output_def.io_manager_key], IOutputManagerDefinition):
        raise DagsterInvalidDefinitionError(
            f'Output "{output_def.name}" for {node.describe_node()} requires io_manager_key '
            f'"{output_def.io_manager_key}", but the resource definition provided is not an '
            "IOutputManagerDefinition"
        )
    output_manager_def = resource_defs[output_def.io_manager_key]
    if (
        output_manager_def
        and isinstance(output_manager_def, IOutputManagerDefinition)
        and output_manager_def.output_config_schema
    ):
        return output_manager_def.output_config_schema.as_field()

    return None


def node_config_field(fields: Mapping[str, Optional[Field]], ignored: bool) -> Optional[Field]:
    trimmed_fields = remove_none_entries(fields)
    if trimmed_fields:
        if ignored:
            return Field(
                Shape(trimmed_fields),
                is_required=False,
                description=(
                    "This op is not present in the current op selection, "
                    "the config values are allowed but ignored."
                ),
            )
        else:
            return Field(Shape(trimmed_fields))
    else:
        return None


def construct_leaf_node_config(
    node: Node,
    handle: NodeHandle,
    dependency_structure: DependencyStructure,
    config_schema: Optional[IDefinitionConfigSchema],
    resource_defs: Mapping[str, ResourceDefinition],
    ignored: bool,
    asset_layer: AssetLayer,
    input_source_assets: Mapping[str, "SourceAsset"],
) -> Optional[Field]:
    return node_config_field(
        {
            "inputs": get_inputs_field(
                node,
                handle,
                dependency_structure,
                resource_defs,
                ignored,
                asset_layer,
                input_source_assets,
            ),
            "outputs": get_outputs_field(node, resource_defs),
            "config": config_schema.as_field() if config_schema else None,
        },
        ignored=ignored,
    )


def define_node_field(
    node: Node,
    handle: NodeHandle,
    dependency_structure: DependencyStructure,
    resource_defs: Mapping[str, ResourceDefinition],
    ignored: bool,
    asset_layer: AssetLayer,
    input_source_assets: Mapping[str, "SourceAsset"],
) -> Optional[Field]:
    # All nodes regardless of compositing status get the same inputs and outputs
    # config. The only thing the varies is on extra element of configuration
    # 1) Vanilla op definition: a 'config' key with the config_schema as the value
    # 2) Graph with field mapping: a 'config' key with the config_schema of
    #    the config mapping (via GraphDefinition#config_schema)
    # 3) Graph without field mapping: an 'ops' key with recursively defined
    #    ops dictionary
    # 4) `configured` graph with field mapping: a 'config' key with the config_schema that was
    #    provided when `configured` was called (via GraphDefinition#config_schema)

    assert isinstance(node, (OpNode, GraphNode)), f"Invalid node type: {type(node)}"

    if isinstance(node, OpNode):
        return construct_leaf_node_config(
            node,
            handle,
            dependency_structure,
            node.definition.config_schema,
            resource_defs,
            ignored,
            asset_layer,
            input_source_assets,
        )

    graph_def = node.definition

    if graph_def.has_config_mapping:
        # has_config_mapping covers cases 2 & 4 from above (only config mapped graphs can
        # be `configured`)...
        return construct_leaf_node_config(
            node,
            handle,
            dependency_structure,
            # ...and in both cases, the correct schema for 'config' key is exposed by this property:
            graph_def.config_schema,
            resource_defs,
            ignored,
            asset_layer,
            input_source_assets,
        )
        # This case omits an 'ops' key, thus if a graph is `configured` or has a field
        # mapping, the user cannot stub any config, inputs, or outputs for inner (child) nodes.
    else:
        fields = {
            "inputs": get_inputs_field(
                node,
                handle,
                dependency_structure,
                resource_defs,
                ignored,
                asset_layer,
                input_source_assets,
            ),
            "outputs": get_outputs_field(node, resource_defs),
            "ops": Field(
                define_node_shape(
                    nodes=graph_def.nodes,
                    ignored_nodes=None,
                    dependency_structure=graph_def.dependency_structure,
                    parent_handle=handle,
                    resource_defs=resource_defs,
                    asset_layer=asset_layer,
                    node_input_source_assets=graph_def.node_input_source_assets,
                )
            ),
        }

        return node_config_field(fields, ignored=ignored)


def define_node_shape(
    nodes: Sequence[Node],
    ignored_nodes: Optional[Sequence[Node]],
    dependency_structure: DependencyStructure,
    resource_defs: Mapping[str, ResourceDefinition],
    asset_layer: AssetLayer,
    node_input_source_assets: Mapping[str, Mapping[str, "SourceAsset"]],
    parent_handle: Optional[NodeHandle] = None,
) -> Shape:
    """Examples of what this method is used to generate the schema for:
    1.
        inputs: ...
        ops:
      >    op1: ...
      >    op2: ...

    2.
        inputs:
        ops:
          graph1: ...
            inputs: ...
            ops:
      >       op1: ...
      >       inner_graph: ...


    """
    ignored_nodes = check.opt_sequence_param(ignored_nodes, "ignored_nodes", of_type=Node)

    fields = {}
    for node in nodes:
        node_field = define_node_field(
            node,
            NodeHandle(node.name, parent_handle),
            dependency_structure,
            resource_defs,
            ignored=False,
            asset_layer=asset_layer,
            input_source_assets=node_input_source_assets.get(node.name, {}),
        )

        if node_field:
            fields[node.name] = node_field

    for node in ignored_nodes:
        node_field = define_node_field(
            node,
            NodeHandle(node.name, parent_handle),
            dependency_structure,
            resource_defs,
            ignored=True,
            asset_layer=asset_layer,
            input_source_assets=node_input_source_assets.get(node.name, {}),
        )
        if node_field:
            fields[node.name] = node_field

    return Shape(fields)


def iterate_node_def_config_types(node_def: NodeDefinition) -> Iterator[ConfigType]:
    if isinstance(node_def, OpDefinition):
        if node_def.has_config_field:
            yield from node_def.get_config_field().config_type.type_iterator()
    elif isinstance(node_def, GraphDefinition):
        for node in node_def.nodes:
            yield from iterate_node_def_config_types(node.definition)

    else:
        check.invariant(f"Unexpected NodeDefinition type {type(node_def)}")


def _gather_all_schemas(node_defs: Sequence[NodeDefinition]) -> Iterator[ConfigType]:
    dagster_types = construct_dagster_type_dictionary(node_defs)
    for dagster_type in list(dagster_types.values()) + list(ALL_RUNTIME_BUILTINS):
        if dagster_type.loader:
            yield from dagster_type.loader.schema_type.type_iterator()


def _gather_all_config_types(
    node_defs: Sequence[NodeDefinition], run_config_schema_type: ConfigType
) -> Iterator[ConfigType]:
    for node_def in node_defs:
        yield from iterate_node_def_config_types(node_def)

    yield from run_config_schema_type.type_iterator()


def construct_config_type_dictionary(
    node_defs: Sequence[NodeDefinition],
    run_config_schema_type: ConfigType,
) -> Tuple[Mapping[str, ConfigType], Mapping[str, ConfigType]]:
    type_dict_by_name = {t.given_name: t for t in ALL_CONFIG_BUILTINS if t.given_name}
    type_dict_by_key = {t.key: t for t in ALL_CONFIG_BUILTINS}
    all_types = list(_gather_all_config_types(node_defs, run_config_schema_type)) + list(
        _gather_all_schemas(node_defs)
    )

    for config_type in all_types:
        name = config_type.given_name
        if name and name in type_dict_by_name:
            if type(config_type) is not type(type_dict_by_name[name]):
                raise DagsterInvalidDefinitionError(
                    "Type names must be unique. You have constructed two different "
                    f'instances of types with the same name "{name}".'
                )
        elif name:
            type_dict_by_name[name] = config_type

        type_dict_by_key[config_type.key] = config_type

    return type_dict_by_name, type_dict_by_key


def _convert_config_classes_inner(configs: Any) -> Any:
    if not isinstance(configs, dict):
        return configs

    return {
        k: (
            {"config": v._convert_to_config_dictionary()}  # noqa: SLF001
            if isinstance(v, Config)
            else _convert_config_classes_inner(v)
        )
        for k, v in configs.items()
    }


def _convert_config_classes(configs: Dict[str, Any]) -> Dict[str, Any]:
    return _convert_config_classes_inner(configs)


class RunConfig:
    """Container for all the configuration that can be passed to a run. Accepts Pythonic definitions
    for op and asset config and resources and converts them under the hood to the appropriate config dictionaries.

    Example usage:

    .. code-block:: python

        class MyAssetConfig(Config):
            a_str: str

        @asset
        def my_asset(config: MyAssetConfig):
            assert config.a_str == "foo"

        materialize(
            [my_asset],
            run_config=RunConfig(
                ops={"my_asset": MyAssetConfig(a_str="foo")}
            )
        )

    """

    def __init__(
        self,
        ops: Optional[Dict[str, Any]] = None,
        resources: Optional[Dict[str, Any]] = None,
        loggers: Optional[Dict[str, Any]] = None,
        execution: Optional[Dict[str, Any]] = None,
    ):
        self.ops = check.opt_dict_param(ops, "ops")
        self.resources = check.opt_dict_param(resources, "resources")
        self.loggers = check.opt_dict_param(loggers, "loggers")
        self.execution = check.opt_dict_param(execution, "execution")

    def to_config_dict(self):
        return {
            "loggers": self.loggers,
            "resources": _convert_config_classes(self.resources),
            "ops": _convert_config_classes(self.ops),
            "execution": self.execution,
        }


CoercibleToRunConfig: TypeAlias = Union[Dict[str, Any], RunConfig]

T = TypeVar("T")


def convert_config_input(inp: Union[CoercibleToRunConfig, T]) -> Union[T, Mapping[str, Any]]:
    if isinstance(inp, RunConfig):
        return inp.to_config_dict()
    else:
        return inp
