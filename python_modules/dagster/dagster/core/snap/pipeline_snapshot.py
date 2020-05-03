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
from dagster.core.definitions import PipelineDefinition
from dagster.serdes import deserialize_value, whitelist_for_serdes

from .config_types import build_config_schema_snapshot
from .dagster_types import DagsterTypeNamespaceSnapshot, build_dagster_type_namespace_snapshot
from .dep_snapshot import (
    DependencyStructureIndex,
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
from .utils import create_snapshot_id


class PipelineIndex:
    def __init__(self, pipeline_snapshot):
        self.pipeline_snapshot = check.inst_param(
            pipeline_snapshot, 'pipeline_snapshot', PipelineSnapshot
        )

        self._solid_defs_snaps_index = {
            sd.name: sd
            for sd in pipeline_snapshot.solid_definitions_snapshot.solid_def_snaps
            + pipeline_snapshot.solid_definitions_snapshot.composite_solid_def_snaps
        }

        self._dagster_type_snaps_by_name_index = {
            dagster_type_snap.name: dagster_type_snap
            for dagster_type_snap in pipeline_snapshot.dagster_type_namespace_snapshot.all_dagster_type_snaps_by_key.values()
            if dagster_type_snap.name
        }

        self.dep_structure_index = DependencyStructureIndex(
            pipeline_snapshot.dep_structure_snapshot
        )

        self._comp_dep_structures = {
            comp_snap.name: DependencyStructureIndex(comp_snap.dep_structure_snapshot)
            for comp_snap in pipeline_snapshot.solid_definitions_snapshot.composite_solid_def_snaps
        }

        self.pipeline_snapshot_id = create_pipeline_snapshot_id(pipeline_snapshot)

    @property
    def name(self):
        return self.pipeline_snapshot.name

    @property
    def description(self):
        return self.pipeline_snapshot.description

    @property
    def tags(self):
        return self.pipeline_snapshot.tags

    def has_dagster_type_name(self, type_name):
        return type_name in self._dagster_type_snaps_by_name_index

    def get_dagster_type_from_name(self, type_name):
        return self._dagster_type_snaps_by_name_index[type_name]

    def get_solid_def_snap(self, solid_def_name):
        check.str_param(solid_def_name, 'solid_def_name')
        return self._solid_defs_snaps_index[solid_def_name]

    def get_dep_structure_index(self, comp_solid_def_name):
        return self._comp_dep_structures[comp_solid_def_name]

    def get_dagster_type_snaps(self):
        dt_namespace = self.pipeline_snapshot.dagster_type_namespace_snapshot
        return list(dt_namespace.all_dagster_type_snaps_by_key.values())

    def has_solid_invocation(self, solid_name):
        return self.dep_structure_index.has_invocation(solid_name)

    def get_default_mode_name(self):
        return self.pipeline_snapshot.mode_def_snaps[0].name

    def has_mode_def(self, name):
        check.str_param(name, 'name')
        for mode_def_snap in self.pipeline_snapshot.mode_def_snaps:
            if mode_def_snap.name == name:
                return True

        return False

    def get_mode_def_snap(self, name):
        check.str_param(name, 'name')
        for mode_def_snap in self.pipeline_snapshot.mode_def_snaps:
            if mode_def_snap.name == name:
                return mode_def_snap

        check.failed('Mode {mode} not found'.format(mode=name))

    @property
    def config_schema_snapshot(self):
        return self.pipeline_snapshot.config_schema_snapshot


def create_pipeline_snapshot_id(snapshot):
    check.inst_param(snapshot, 'snapshot', PipelineSnapshot)
    return create_snapshot_id(snapshot)


@whitelist_for_serdes
class PipelineSnapshot(
    namedtuple(
        '_PipelineSnapshot',
        'name description tags '
        'config_schema_snapshot dagster_type_namespace_snapshot solid_definitions_snapshot '
        'dep_structure_snapshot mode_def_snaps',
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
    ):
        return super(PipelineSnapshot, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            description=check.opt_str_param(description, 'description'),
            tags=check.opt_dict_param(tags, 'tags'),
            config_schema_snapshot=check.inst_param(
                config_schema_snapshot, 'config_schema_snapshot', ConfigSchemaSnapshot
            ),
            dagster_type_namespace_snapshot=check.inst_param(
                dagster_type_namespace_snapshot,
                'dagster_type_namespace_snapshot',
                DagsterTypeNamespaceSnapshot,
            ),
            solid_definitions_snapshot=check.inst_param(
                solid_definitions_snapshot, 'solid_definitions_snapshot', SolidDefinitionsSnapshot
            ),
            dep_structure_snapshot=check.inst_param(
                dep_structure_snapshot, 'dep_structure_snapshot', DependencyStructureSnapshot
            ),
            mode_def_snaps=check.list_param(mode_def_snaps, 'mode_def_snaps', of_type=ModeDefSnap),
        )

    @staticmethod
    def from_pipeline_def(pipeline_def):
        check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
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
                    md, pipeline_def.get_environment_schema(md.name).environment_type.key
                )
                for md in pipeline_def.mode_definitions
            ],
        )

    def get_solid_def_snap(self, solid_def_name):
        check.str_param(solid_def_name, 'solid_def_name')
        for solid_def_snap in (
            self.solid_definitions_snapshot.solid_def_snaps
            + self.solid_definitions_snapshot.composite_solid_def_snaps
        ):
            if solid_def_snap.name == solid_def_name:
                return solid_def_snap

        check.failed('not found')

    def has_solid_name(self, solid_name):
        check.str_param(solid_name, 'solid_name')
        for solid_snap in self.dep_structure_snapshot.solid_invocation_snaps:
            if solid_snap.solid_name == solid_name:
                return True
        return False

    def get_config_type_from_solid_def_snap(self, solid_def_snap):
        check.inst_param(solid_def_snap, 'solid_def_snap', (SolidDefSnap, CompositeSolidDefSnap))
        if solid_def_snap.config_field_snap:
            config_type_key = solid_def_snap.config_field_snap.type_key
            if self.config_schema_snapshot.has_config_snap(config_type_key):
                return construct_config_type_from_snap(
                    self.config_schema_snapshot.get_config_snap(config_type_key),
                    self.config_schema_snapshot.all_config_snaps_by_key,
                )
        return None


def _construct_enum_from_snap(config_type_snap):
    check.list_param(config_type_snap.enum_values, 'enum_values', ConfigEnumValueSnap)

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
    check.list_param(config_type_snap.fields, 'config_field_snap', ConfigFieldSnap)

    return Selector(
        fields=_construct_fields(config_type_snap, config_snap_map),
        description=config_type_snap.description,
    )


def _construct_shape_from_snap(config_type_snap, config_snap_map):
    check.list_param(config_type_snap.fields, 'config_field_snap', ConfigFieldSnap)

    return Shape(
        fields=_construct_fields(config_type_snap, config_snap_map),
        description=config_type_snap.description,
    )


def _construct_permissive_from_snap(config_type_snap, config_snap_map):
    check.opt_list_param(config_type_snap.fields, 'config_field_snap', ConfigFieldSnap)

    return Permissive(
        fields=_construct_fields(config_type_snap, config_snap_map),
        description=config_type_snap.description,
    )


def _construct_scalar_union_from_snap(config_type_snap, config_snap_map):
    check.list_param(config_type_snap.type_param_keys, 'type_param_keys', str)
    check.invariant(
        len(config_type_snap.type_param_keys) == 2,
        'Expect SCALAR_UNION to provide a scalar key and a non scalar key. Snapshot Provided: {}'.format(
            config_type_snap.type_param_keys
        ),
    )

    return ScalarUnion(
        scalar_type=construct_config_type_from_snap(
            config_snap_map[config_type_snap.type_param_keys[0]], config_snap_map
        ),
        non_scalar_type=construct_config_type_from_snap(
            config_snap_map[config_type_snap.type_param_keys[1]], config_snap_map
        ),
    )


def _construct_array_from_snap(config_type_snap, config_snap_map):
    check.list_param(config_type_snap.type_param_keys, 'type_param_keys', str)
    check.invariant(
        len(config_type_snap.type_param_keys) == 1,
        'Expect ARRAY to provide a single inner type. Snapshot provided: {}'.format(
            config_type_snap.type_param_keys
        ),
    )

    return Array(
        inner_type=construct_config_type_from_snap(
            config_snap_map[config_type_snap.type_param_keys[0]], config_snap_map
        )
    )


def _construct_noneable_from_snap(config_type_snap, config_snap_map):
    check.list_param(config_type_snap.type_param_keys, 'type_param_keys', str)
    check.invariant(
        len(config_type_snap.type_param_keys) == 1,
        'Expect NONEABLE to provide a single inner type. Snapshot provided: {}'.format(
            config_type_snap.type_param_keys
        ),
    )
    return Noneable(
        construct_config_type_from_snap(
            config_snap_map[config_type_snap.type_param_keys[0]], config_snap_map
        )
    )


def construct_config_type_from_snap(config_type_snap, config_snap_map):
    check.inst_param(config_type_snap, 'config_type_snap', ConfigTypeSnap)
    check.dict_param(config_snap_map, 'config_snap_map', key_type=str, value_type=ConfigTypeSnap)

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
    check.failed('Could not evaluate config type snap kind: {}'.format(config_type_snap.kind))
