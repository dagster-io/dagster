import hashlib
from collections import namedtuple

from dagster import check
from dagster.core.definitions import PipelineDefinition
from dagster.serdes import serialize_dagster_namedtuple, whitelist_for_serdes

from .config_types import ConfigSchemaSnapshot, build_config_schema_snapshot
from .dagster_types import DagsterTypeNamespaceSnapshot, build_dagster_type_namespace_snapshot
from .dep_snapshot import (
    DependencyStructureIndex,
    DependencyStructureSnapshot,
    build_dep_structure_snapshot_from_icontains_solids,
)
from .mode import ModeDefSnap, build_mode_def_snap
from .solid import SolidDefinitionsSnapshot, build_solid_definitions_snapshot


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

        self.dep_structure_index = DependencyStructureIndex(
            pipeline_snapshot.dep_structure_snapshot
        )

        self._comp_dep_structures = {
            comp_snap.name: DependencyStructureIndex(comp_snap.dep_structure_snapshot)
            for comp_snap in pipeline_snapshot.solid_definitions_snapshot.composite_solid_def_snaps
        }

    @property
    def name(self):
        return self.pipeline_snapshot.name

    @property
    def description(self):
        return self.pipeline_snapshot.description

    @property
    def tags(self):
        return self.pipeline_snapshot.tags

    def get_solid_def_snap(self, solid_def_name):
        check.str_param(solid_def_name, 'solid_def_name')
        return self._solid_defs_snaps_index[solid_def_name]

    def get_dep_structure_index(self, comp_solid_def_name):
        return self._comp_dep_structures[comp_solid_def_name]

    def get_dagster_type_snaps(self):
        dt_namespace = self.pipeline_snapshot.dagster_type_namespace_snapshot
        return list(dt_namespace.all_dagster_type_snaps_by_key.values())


def create_pipeline_snapshot_id(snapshot):
    json_rep = serialize_dagster_namedtuple(snapshot)
    m = hashlib.sha1()  # so that hexdigest is 40, not 64 bytes
    m.update(json_rep.encode())
    return m.hexdigest()


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
            mode_def_snaps=list(map(build_mode_def_snap, pipeline_def.mode_definitions)),
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
