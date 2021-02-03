from collections import namedtuple

from dagster import Field, Permissive, Selector, Shape, check
from dagster.config.config_type import (
    Array,
    ConfigTypeKind,
    Enum,
    EnumValue,
    Noneable,
    ScalarUnion,
    get_builtin_scalar_by_name,
)
from dagster.config.field_utils import FIELD_NO_DEFAULT_PROVIDED
from dagster.config.snap import (
    ConfigEnumValueSnap,
    ConfigFieldSnap,
    ConfigSchemaSnapshot,
    ConfigTypeSnap,
)
from dagster.core.definitions.pipeline import PipelineDefinition, PipelineSubsetDefinition
from dagster.core.utils import toposort_flatten
from dagster.serdes import create_snapshot_id, deserialize_value, whitelist_for_serdes

from .config_types import build_config_schema_snapshot
from .dagster_types import DagsterTypeNamespaceSnapshot, build_dagster_type_namespace_snapshot
from .dep_snapshot import (
    DependencyStructureSnapshot,
    build_dep_structure_snapshot_from_icontains_solids,
)
from .mode import ModeDefSnap, build_mode_def_snap
from .solid import (
    CompositeSolidDefSnap,
    SolidDefSnap,
    SolidDefinitionsSnapshot,
    build_solid_definitions_snapshot,
)


def create_pipeline_snapshot_id(snapshot):
    check.inst_param(snapshot, "snapshot", PipelineSnapshot)
    return create_snapshot_id(snapshot)


@whitelist_for_serdes
class PipelineSnapshot(
    namedtuple(
        "_PipelineSnapshot",
        "name description tags "
        "config_schema_snapshot dagster_type_namespace_snapshot solid_definitions_snapshot "
        "dep_structure_snapshot mode_def_snaps lineage_snapshot",
    )
):
    def __new__(
        cls,
        name,
        description,
        tags,
        config_schema_snapshot,
        dagster_type_namespace_snapshot,
        solid_definitions_snapshot,
        dep_structure_snapshot,
        mode_def_snaps,
        lineage_snapshot=None,
    ):
        return super(PipelineSnapshot, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            description=check.opt_str_param(description, "description"),
            tags=check.opt_dict_param(tags, "tags"),
            config_schema_snapshot=check.inst_param(
                config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot
            ),
            dagster_type_namespace_snapshot=check.inst_param(
                dagster_type_namespace_snapshot,
                "dagster_type_namespace_snapshot",
                DagsterTypeNamespaceSnapshot,
            ),
            solid_definitions_snapshot=check.inst_param(
                solid_definitions_snapshot, "solid_definitions_snapshot", SolidDefinitionsSnapshot
            ),
            dep_structure_snapshot=check.inst_param(
                dep_structure_snapshot, "dep_structure_snapshot", DependencyStructureSnapshot
            ),
            mode_def_snaps=check.list_param(mode_def_snaps, "mode_def_snaps", of_type=ModeDefSnap),
            lineage_snapshot=check.opt_inst_param(
                lineage_snapshot, "lineage_snapshot", PipelineSnapshotLineage
            ),
        )

    @classmethod
    def from_pipeline_def(cls, pipeline_def):
        check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
        lineage = None
        if isinstance(pipeline_def, PipelineSubsetDefinition):
            lineage = PipelineSnapshotLineage(
                parent_snapshot_id=create_pipeline_snapshot_id(
                    cls.from_pipeline_def(pipeline_def.parent_pipeline_def)
                ),
                solid_selection=pipeline_def.solid_selection,
                solids_to_execute=pipeline_def.solids_to_execute,
            )

        return PipelineSnapshot(
            name=pipeline_def.name,
            description=pipeline_def.description,
            tags=pipeline_def.tags,
            config_schema_snapshot=build_config_schema_snapshot(pipeline_def),
            dagster_type_namespace_snapshot=build_dagster_type_namespace_snapshot(pipeline_def),
            solid_definitions_snapshot=build_solid_definitions_snapshot(pipeline_def),
            dep_structure_snapshot=build_dep_structure_snapshot_from_icontains_solids(pipeline_def),
            mode_def_snaps=[
                build_mode_def_snap(
                    md, pipeline_def.get_run_config_schema(md.name).environment_type.key
                )
                for md in pipeline_def.mode_definitions
            ],
            lineage_snapshot=lineage,
        )

    def get_solid_def_snap(self, solid_def_name):
        check.str_param(solid_def_name, "solid_def_name")
        for solid_def_snap in (
            self.solid_definitions_snapshot.solid_def_snaps
            + self.solid_definitions_snapshot.composite_solid_def_snaps
        ):
            if solid_def_snap.name == solid_def_name:
                return solid_def_snap

        check.failed("not found")

    def has_solid_name(self, solid_name):
        check.str_param(solid_name, "solid_name")
        for solid_snap in self.dep_structure_snapshot.solid_invocation_snaps:
            if solid_snap.solid_name == solid_name:
                return True
        return False

    def get_config_type_from_solid_def_snap(self, solid_def_snap):
        check.inst_param(solid_def_snap, "solid_def_snap", (SolidDefSnap, CompositeSolidDefSnap))
        if solid_def_snap.config_field_snap:
            config_type_key = solid_def_snap.config_field_snap.type_key
            if self.config_schema_snapshot.has_config_snap(config_type_key):
                return construct_config_type_from_snap(
                    self.config_schema_snapshot.get_config_snap(config_type_key),
                    self.config_schema_snapshot.all_config_snaps_by_key,
                )
        return None

    @property
    def solid_names(self):
        return [ss.solid_name for ss in self.dep_structure_snapshot.solid_invocation_snaps]

    @property
    def solid_names_in_topological_order(self):
        upstream_outputs = {}

        for solid_invocation_snap in self.dep_structure_snapshot.solid_invocation_snaps:
            solid_name = solid_invocation_snap.solid_name
            upstream_outputs[solid_name] = {
                upstream_output_snap.solid_name
                for input_dep_snap in solid_invocation_snap.input_dep_snaps
                for upstream_output_snap in input_dep_snap.upstream_output_snaps
            }

        return toposort_flatten(upstream_outputs)


def _construct_enum_from_snap(config_type_snap):
    check.list_param(config_type_snap.enum_values, "enum_values", ConfigEnumValueSnap)

    return Enum(
        name=config_type_snap.key,
        enum_values=[
            EnumValue(enum_value_snap.value, description=enum_value_snap.description)
            for enum_value_snap in config_type_snap.enum_values
        ],
    )


def _construct_fields(config_type_snap, config_snap_map):
    return {
        field.name: Field(
            construct_config_type_from_snap(config_snap_map[field.type_key], config_snap_map),
            description=field.description,
            is_required=field.is_required,
            default_value=deserialize_value(field.default_value_as_json_str)
            if field.default_provided
            else FIELD_NO_DEFAULT_PROVIDED,
        )
        for field in config_type_snap.fields
    }


def _construct_selector_from_snap(config_type_snap, config_snap_map):
    check.list_param(config_type_snap.fields, "config_field_snap", ConfigFieldSnap)

    return Selector(
        fields=_construct_fields(config_type_snap, config_snap_map),
        description=config_type_snap.description,
    )


def _construct_shape_from_snap(config_type_snap, config_snap_map):
    check.list_param(config_type_snap.fields, "config_field_snap", ConfigFieldSnap)

    return Shape(
        fields=_construct_fields(config_type_snap, config_snap_map),
        description=config_type_snap.description,
    )


def _construct_permissive_from_snap(config_type_snap, config_snap_map):
    check.opt_list_param(config_type_snap.fields, "config_field_snap", ConfigFieldSnap)

    return Permissive(
        fields=_construct_fields(config_type_snap, config_snap_map),
        description=config_type_snap.description,
    )


def _construct_scalar_union_from_snap(config_type_snap, config_snap_map):
    check.list_param(config_type_snap.type_param_keys, "type_param_keys", str)
    check.invariant(
        len(config_type_snap.type_param_keys) == 2,
        "Expect SCALAR_UNION to provide a scalar key and a non scalar key. Snapshot Provided: {}".format(
            config_type_snap.type_param_keys
        ),
    )

    return ScalarUnion(
        scalar_type=construct_config_type_from_snap(
            config_snap_map[config_type_snap.type_param_keys[0]], config_snap_map
        ),
        non_scalar_schema=construct_config_type_from_snap(
            config_snap_map[config_type_snap.type_param_keys[1]], config_snap_map
        ),
    )


def _construct_array_from_snap(config_type_snap, config_snap_map):
    check.list_param(config_type_snap.type_param_keys, "type_param_keys", str)
    check.invariant(
        len(config_type_snap.type_param_keys) == 1,
        "Expect ARRAY to provide a single inner type. Snapshot provided: {}".format(
            config_type_snap.type_param_keys
        ),
    )

    return Array(
        inner_type=construct_config_type_from_snap(
            config_snap_map[config_type_snap.type_param_keys[0]], config_snap_map
        )
    )


def _construct_noneable_from_snap(config_type_snap, config_snap_map):
    check.list_param(config_type_snap.type_param_keys, "type_param_keys", str)
    check.invariant(
        len(config_type_snap.type_param_keys) == 1,
        "Expect NONEABLE to provide a single inner type. Snapshot provided: {}".format(
            config_type_snap.type_param_keys
        ),
    )
    return Noneable(
        construct_config_type_from_snap(
            config_snap_map[config_type_snap.type_param_keys[0]], config_snap_map
        )
    )


def construct_config_type_from_snap(config_type_snap, config_snap_map):
    check.inst_param(config_type_snap, "config_type_snap", ConfigTypeSnap)
    check.dict_param(config_snap_map, "config_snap_map", key_type=str, value_type=ConfigTypeSnap)

    if config_type_snap.kind in (ConfigTypeKind.SCALAR, ConfigTypeKind.ANY):
        return get_builtin_scalar_by_name(config_type_snap.key)
    elif config_type_snap.kind == ConfigTypeKind.ENUM:
        return _construct_enum_from_snap(config_type_snap)
    elif config_type_snap.kind == ConfigTypeKind.SELECTOR:
        return _construct_selector_from_snap(config_type_snap, config_snap_map)
    elif config_type_snap.kind == ConfigTypeKind.STRICT_SHAPE:
        return _construct_shape_from_snap(config_type_snap, config_snap_map)
    elif config_type_snap.kind == ConfigTypeKind.PERMISSIVE_SHAPE:
        return _construct_permissive_from_snap(config_type_snap, config_snap_map)
    elif config_type_snap.kind == ConfigTypeKind.SCALAR_UNION:
        return _construct_scalar_union_from_snap(config_type_snap, config_snap_map)
    elif config_type_snap.kind == ConfigTypeKind.ARRAY:
        return _construct_array_from_snap(config_type_snap, config_snap_map)
    elif config_type_snap.kind == ConfigTypeKind.NONEABLE:
        return _construct_noneable_from_snap(config_type_snap, config_snap_map)
    check.failed("Could not evaluate config type snap kind: {}".format(config_type_snap.kind))


@whitelist_for_serdes
class PipelineSnapshotLineage(
    namedtuple(
        "_PipelineSnapshotLineage",
        "parent_snapshot_id solid_selection solids_to_execute",
    )
):
    def __new__(cls, parent_snapshot_id, solid_selection=None, solids_to_execute=None):
        check.opt_set_param(solids_to_execute, "solids_to_execute", of_type=str)
        return super(PipelineSnapshotLineage, cls).__new__(
            cls,
            check.str_param(parent_snapshot_id, parent_snapshot_id),
            solid_selection,
            solids_to_execute,
        )
