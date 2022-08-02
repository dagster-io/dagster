from typing import AbstractSet, Any, Iterator, Mapping, NamedTuple, Optional, Sequence, Tuple, cast

from dagster._config import (
    ALL_CONFIG_BUILTINS,
    Array,
    ConfigType,
    Field,
    Permissive,
    Selector,
    Shape,
    iterate_config_types,
)
from dagster._core.definitions.asset_layer import AssetLayer
from dagster._core.definitions.executor_definition import (
    ExecutorDefinition,
    execute_in_process_executor,
    in_process_executor,
)
from dagster._core.definitions.input import InputDefinition
from dagster._core.definitions.output import OutputDefinition
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.storage.output_manager import IOutputManagerDefinition
from dagster._core.storage.root_input_manager import IInputManagerDefinition
from dagster._core.types.dagster_type import ALL_RUNTIME_BUILTINS, construct_dagster_type_dictionary
from dagster._utils import check

from .configurable import ConfigurableDefinition
from .definition_config_schema import IDefinitionConfigSchema
from .dependency import DependencyStructure, Node, NodeHandle, SolidInputHandle
from .graph_definition import GraphDefinition
from .logger_definition import LoggerDefinition
from .mode import ModeDefinition
from .resource_definition import ResourceDefinition
from .solid_definition import NodeDefinition, SolidDefinition


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
    pipeline_name: str
    solids: Sequence[Node]
    graph_def: GraphDefinition
    dependency_structure: DependencyStructure
    mode_definition: ModeDefinition
    logger_defs: Mapping[str, LoggerDefinition]
    ignored_solids: Sequence[Node]
    required_resources: AbstractSet[str]
    is_using_graph_job_op_apis: bool
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
        if executor_def == in_process_executor:  # pylint: disable=comparison-with-callable
            default_in_process = True

    selector = selector_for_named_defs(executor_defs)

    if default_in_process:
        return Field(
            selector, default_value={in_process_executor.name: {}}, description=description
        )

    # If we are using the execute_in_process executor, then ignore all executor config.
    if (
        len(executor_defs) == 1
        and executor_defs[0]  # pylint: disable=comparison-with-callable
        == execute_in_process_executor
    ):
        return Field(Permissive(), is_required=False, default_value={}, description=description)

    return Field(selector, description=description)


def define_single_execution_field(executor_def: ExecutorDefinition, description: str) -> Field:
    return def_config_field(executor_def, description=description)


def define_run_config_schema_type(creation_data: RunConfigSchemaCreationData) -> ConfigType:
    execution_field = (
        define_execution_field(
            creation_data.mode_definition.executor_defs,
            "Configure how steps are executed within a run.",
        )
        if not creation_data.is_using_graph_job_op_apis
        else define_single_execution_field(
            creation_data.mode_definition.executor_defs[0],
            "Configure how steps are executed within a run.",
        )
    )

    top_level_node = Node(
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
                creation_data.mode_definition.resource_defs,
                creation_data.required_resources,
            ),
            description="Configure how shared resources are implemented within a run.",
        ),
        "inputs": get_inputs_field(
            solid=top_level_node,
            handle=NodeHandle(top_level_node.name, parent=None),
            dependency_structure=creation_data.dependency_structure,
            resource_defs=creation_data.mode_definition.resource_defs,
            solid_ignored=False,
            direct_inputs=creation_data.direct_inputs,
            asset_layer=creation_data.asset_layer,
            is_using_graph_job_op_apis=creation_data.is_using_graph_job_op_apis,
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
            define_solid_dictionary_cls(
                solids=creation_data.solids,
                ignored_solids=creation_data.ignored_solids,
                dependency_structure=creation_data.dependency_structure,
                resource_defs=creation_data.mode_definition.resource_defs,
                is_using_graph_job_op_apis=creation_data.is_using_graph_job_op_apis,
                asset_layer=creation_data.asset_layer,
            ),
            description="Configure runtime parameters for ops or assets.",
        )

    if creation_data.is_using_graph_job_op_apis:
        fields["ops"] = nodes_field
        field_aliases = {"ops": "solids"}
    else:
        fields["solids"] = nodes_field
        field_aliases = {"solids": "ops"}

    return Shape(
        fields=remove_none_entries(fields),
        field_aliases=field_aliases,
    )


# Common pattern for a set of named definitions (e.g. executors)
# to build a selector so that one of them is selected
def selector_for_named_defs(named_defs) -> Selector:
    return Selector({named_def.name: def_config_field(named_def) for named_def in named_defs})


def get_inputs_field(
    solid: Node,
    handle: NodeHandle,
    dependency_structure: DependencyStructure,
    resource_defs: Mapping[str, ResourceDefinition],
    solid_ignored: bool,
    asset_layer: AssetLayer,
    is_using_graph_job_op_apis: bool,
    direct_inputs: Optional[Mapping[str, Any]] = None,
):
    direct_inputs = check.opt_mapping_param(direct_inputs, "direct_inputs")
    inputs_field_fields = {}
    for name, inp in solid.definition.input_dict.items():
        inp_handle = SolidInputHandle(solid, inp)
        has_upstream = input_has_upstream(dependency_structure, inp_handle, solid, name)
        if inp.input_manager_key:
            input_field = get_input_manager_input_field(solid, inp, resource_defs)
        elif (
            # if you have asset definitions, input will be loaded from the source asset
            asset_layer.has_assets_defs
            and asset_layer.asset_key_for_input(handle, name)
            and not has_upstream
        ):
            input_field = None
        elif name in direct_inputs and not has_upstream:
            input_field = None
        elif inp.root_manager_key and not has_upstream:
            input_field = get_input_manager_input_field(solid, inp, resource_defs)
        elif inp.dagster_type.loader and not has_upstream:
            input_field = get_type_loader_input_field(solid, name, inp)
        else:
            input_field = None

        if input_field:
            inputs_field_fields[name] = input_field

    if not inputs_field_fields:
        return None
    if solid_ignored:
        node_type = "op" if is_using_graph_job_op_apis else "solid"
        return Field(
            Shape(inputs_field_fields),
            is_required=False,
            description=f"This {node_type} is not present in the current {node_type} selection, "
            "the input config values are allowed but ignored.",
        )
    else:
        return Field(Shape(inputs_field_fields))


def input_has_upstream(
    dependency_structure: DependencyStructure,
    input_handle: SolidInputHandle,
    solid: Node,
    input_name: str,
) -> bool:
    return dependency_structure.has_deps(input_handle) or solid.container_maps_input(input_name)


def get_input_manager_input_field(
    solid: Node,
    input_def: InputDefinition,
    resource_defs: Mapping[str, ResourceDefinition],
) -> Optional[Field]:
    if input_def.root_manager_key:
        if input_def.root_manager_key not in resource_defs:
            raise DagsterInvalidDefinitionError(
                f"Input '{input_def.name}' for {solid.describe_node()} requires root_manager_key "
                f"'{input_def.root_manager_key}', but no resource has been provided. Please include a "
                f"resource definition for that key in the provided resource_defs."
            )

        root_manager = resource_defs[input_def.root_manager_key]
        if not isinstance(root_manager, IInputManagerDefinition):
            raise DagsterInvalidDefinitionError(
                f"Input '{input_def.name}' for {solid.describe_node()} requires root_manager_key "
                f"'{input_def.root_manager_key}', but the resource definition provided is not an "
                "IInputManagerDefinition"
            )

        input_config_schema = root_manager.input_config_schema
        if input_config_schema:
            return input_config_schema.as_field()
        return None
    elif input_def.input_manager_key:
        if input_def.input_manager_key not in resource_defs:
            raise DagsterInvalidDefinitionError(
                f"Input '{input_def.name}' for {solid.describe_node()} requires input_manager_key "
                f"'{input_def.input_manager_key}', but no resource has been provided. Please include a "
                f"resource definition for that key in the provided resource_defs."
            )

        input_manager = resource_defs[input_def.input_manager_key]
        if not isinstance(input_manager, IInputManagerDefinition):
            raise DagsterInvalidDefinitionError(
                f"Input '{input_def.name}' for {solid.describe_node()} requires input_manager_key "
                f"'{input_def.input_manager_key}', but the resource definition provided is not an "
                "IInputManagerDefinition"
            )

        input_config_schema = input_manager.input_config_schema
        if input_config_schema:
            return input_config_schema.as_field()
        return None

    return None


def get_type_loader_input_field(solid: Node, input_name: str, input_def: InputDefinition) -> Field:
    loader = check.not_none(input_def.dagster_type.loader)
    return Field(
        loader.schema_type,
        is_required=(
            not solid.definition.input_has_default(input_name) and not input_def.root_manager_key
        ),
    )


def get_outputs_field(
    solid: Node,
    resource_defs: Mapping[str, ResourceDefinition],
) -> Optional[Field]:

    # if any outputs have configurable output managers, use those for the schema and ignore all type
    # materializers
    output_manager_fields = {}
    for name, output_def in solid.definition.output_dict.items():
        output_manager_output_field = get_output_manager_output_field(
            solid, output_def, resource_defs
        )
        if output_manager_output_field:
            output_manager_fields[name] = output_manager_output_field

    if output_manager_fields:
        return Field(Shape(output_manager_fields))

    # otherwise, use any type materializers for the schema
    type_materializer_fields = {}
    for name, output_def in solid.definition.output_dict.items():
        type_output_field = get_type_output_field(output_def)
        if type_output_field:
            type_materializer_fields[name] = type_output_field

    if type_materializer_fields:
        return Field(Array(Shape(type_materializer_fields)), is_required=False)

    return None


def get_output_manager_output_field(
    solid: Node, output_def: OutputDefinition, resource_defs: Mapping[str, ResourceDefinition]
) -> Optional[ConfigType]:
    if output_def.io_manager_key not in resource_defs:
        raise DagsterInvalidDefinitionError(
            f'Output "{output_def.name}" for {solid.describe_node()} requires io_manager_key '
            f'"{output_def.io_manager_key}", but no resource has been provided. Please include a '
            f"resource definition for that key in the provided resource_defs."
        )
    if not isinstance(resource_defs[output_def.io_manager_key], IOutputManagerDefinition):
        raise DagsterInvalidDefinitionError(
            f'Output "{output_def.name}" for {solid.describe_node()} requires io_manager_key '
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


def get_type_output_field(output_def: OutputDefinition) -> Optional[Field]:
    if output_def.dagster_type.materializer:
        return Field(output_def.dagster_type.materializer.schema_type, is_required=False)

    return None


def solid_config_field(
    fields: Mapping[str, Optional[Field]], ignored: bool, is_using_graph_job_op_apis: bool
) -> Optional[Field]:
    field_aliases = {"ops": "solids"} if is_using_graph_job_op_apis else {"solids": "ops"}
    trimmed_fields = remove_none_entries(fields)
    if trimmed_fields:
        if ignored:
            node_type = "op" if is_using_graph_job_op_apis else "solid"
            return Field(
                Shape(trimmed_fields, field_aliases=field_aliases),
                is_required=False,
                description=f"This {node_type} is not present in the current {node_type} selection, "
                "the config values are allowed but ignored.",
            )
        else:
            return Field(Shape(trimmed_fields, field_aliases=field_aliases))
    else:
        return None


def construct_leaf_solid_config(
    solid: Node,
    handle: NodeHandle,
    dependency_structure: DependencyStructure,
    config_schema: Optional[IDefinitionConfigSchema],
    resource_defs: Mapping[str, ResourceDefinition],
    ignored: bool,
    is_using_graph_job_op_apis: bool,
    asset_layer: AssetLayer,
) -> Optional[Field]:
    return solid_config_field(
        {
            "inputs": get_inputs_field(
                solid,
                handle,
                dependency_structure,
                resource_defs,
                ignored,
                asset_layer,
                is_using_graph_job_op_apis,
            ),
            "outputs": get_outputs_field(solid, resource_defs),
            "config": config_schema.as_field() if config_schema else None,
        },
        ignored=ignored,
        is_using_graph_job_op_apis=is_using_graph_job_op_apis,
    )


def define_isolid_field(
    solid: Node,
    handle: NodeHandle,
    dependency_structure: DependencyStructure,
    resource_defs: Mapping[str, ResourceDefinition],
    ignored: bool,
    is_using_graph_job_op_apis: bool,
    asset_layer: AssetLayer,
) -> Optional[Field]:

    # All solids regardless of compositing status get the same inputs and outputs
    # config. The only thing the varies is on extra element of configuration
    # 1) Vanilla solid definition: a 'config' key with the config_schema as the value
    # 2) Composite with field mapping: a 'config' key with the config_schema of
    #    the config mapping (via CompositeSolidDefinition#config_schema)
    # 3) Composite without field mapping: a 'solids' key with recursively defined
    #    solids dictionary
    # 4) `configured` composite with field mapping: a 'config' key with the config_schema that was
    #    provided when `configured` was called (via CompositeSolidDefinition#config_schema)

    if isinstance(solid.definition, SolidDefinition):
        return construct_leaf_solid_config(
            solid,
            handle,
            dependency_structure,
            solid.definition.config_schema,
            resource_defs,
            ignored,
            is_using_graph_job_op_apis,
            asset_layer,
        )

    graph_def = solid.definition.ensure_graph_def()

    if graph_def.has_config_mapping:
        # has_config_mapping covers cases 2 & 4 from above (only config mapped composite solids can
        # be `configured`)...
        return construct_leaf_solid_config(
            solid,
            handle,
            dependency_structure,
            # ...and in both cases, the correct schema for 'config' key is exposed by this property:
            graph_def.config_schema,
            resource_defs,
            ignored,
            is_using_graph_job_op_apis,
            asset_layer,
        )
        # This case omits a 'solids' key, thus if a composite solid is `configured` or has a field
        # mapping, the user cannot stub any config, inputs, or outputs for inner (child) solids.
    else:
        fields = {
            "inputs": get_inputs_field(
                solid,
                handle,
                dependency_structure,
                resource_defs,
                ignored,
                asset_layer,
                is_using_graph_job_op_apis,
            ),
            "outputs": get_outputs_field(solid, resource_defs),
        }
        nodes_field = Field(
            define_solid_dictionary_cls(
                solids=graph_def.solids,
                ignored_solids=None,
                dependency_structure=graph_def.dependency_structure,
                parent_handle=handle,
                resource_defs=resource_defs,
                is_using_graph_job_op_apis=is_using_graph_job_op_apis,
                asset_layer=asset_layer,
            )
        )
        if is_using_graph_job_op_apis:
            fields["ops"] = nodes_field
        else:
            fields["solids"] = nodes_field

        return solid_config_field(
            fields, ignored=ignored, is_using_graph_job_op_apis=is_using_graph_job_op_apis
        )


def define_solid_dictionary_cls(
    solids: Sequence[Node],
    ignored_solids: Optional[Sequence[Node]],
    dependency_structure: DependencyStructure,
    resource_defs: Mapping[str, ResourceDefinition],
    is_using_graph_job_op_apis: bool,
    asset_layer: AssetLayer,
    parent_handle: Optional[NodeHandle] = None,
) -> Shape:
    ignored_solids = check.opt_list_param(ignored_solids, "ignored_solids", of_type=Node)

    fields = {}
    for solid in solids:
        solid_field = define_isolid_field(
            solid,
            NodeHandle(solid.name, parent_handle),
            dependency_structure,
            resource_defs,
            ignored=False,
            is_using_graph_job_op_apis=is_using_graph_job_op_apis,
            asset_layer=asset_layer,
        )

        if solid_field:
            fields[solid.name] = solid_field

    for solid in ignored_solids:
        solid_field = define_isolid_field(
            solid,
            NodeHandle(solid.name, parent_handle),
            dependency_structure,
            resource_defs,
            ignored=True,
            is_using_graph_job_op_apis=is_using_graph_job_op_apis,
            asset_layer=asset_layer,
        )
        if solid_field:
            fields[solid.name] = solid_field

    field_aliases = {"ops": "solids"} if is_using_graph_job_op_apis else {"solids": "ops"}
    return Shape(fields, field_aliases=field_aliases)


def iterate_node_def_config_types(node_def: NodeDefinition) -> Iterator[ConfigType]:
    if isinstance(node_def, SolidDefinition):
        if node_def.has_config_field:
            yield from iterate_config_types(node_def.get_config_field().config_type)
    elif isinstance(node_def, GraphDefinition):
        for solid in node_def.solids:
            yield from iterate_node_def_config_types(solid.definition)

    else:
        check.invariant("Unexpected NodeDefinition type {type}".format(type=type(node_def)))


def _gather_all_schemas(node_defs: Sequence[NodeDefinition]) -> Iterator[ConfigType]:
    dagster_types = construct_dagster_type_dictionary(node_defs)
    for dagster_type in list(dagster_types.values()) + list(ALL_RUNTIME_BUILTINS):
        if dagster_type.loader:
            yield from iterate_config_types(dagster_type.loader.schema_type)
        if dagster_type.materializer:
            yield from iterate_config_types(dagster_type.materializer.schema_type)


def _gather_all_config_types(
    node_defs: Sequence[NodeDefinition], run_config_schema_type: ConfigType
) -> Iterator[ConfigType]:
    for node_def in node_defs:
        yield from iterate_node_def_config_types(node_def)

    yield from iterate_config_types(run_config_schema_type)


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
                    (
                        "Type names must be unique. You have constructed two different "
                        'instances of types with the same name "{name}".'
                    ).format(name=name)
                )
        elif name:
            type_dict_by_name[name] = config_type

        type_dict_by_key[config_type.key] = config_type

    return type_dict_by_name, type_dict_by_key
