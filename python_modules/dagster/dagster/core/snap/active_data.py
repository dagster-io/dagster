from collections import OrderedDict, namedtuple

from dagster import check
from dagster.core.definitions import PipelineDefinition, PresetDefinition, RepositoryDefinition
from dagster.serdes import whitelist_for_serdes

from .pipeline_snapshot import PipelineIndex, PipelineSnapshot


class RepositoryIndex:
    def __init__(self, active_repository_data):
        self.active_repository_data = check.inst_param(
            active_repository_data, 'active_repository_data', ActiveRepositoryData
        )
        self._pipeline_index_map = OrderedDict(
            (pipeline_snapshot.name, PipelineIndex(pipeline_snapshot))
            for pipeline_snapshot in active_repository_data.pipeline_snapshots
        )

    def get_pipeline_index(self, pipeline_name):
        return self._pipeline_index_map[pipeline_name]

    def has_pipeline(self, pipeline_name):
        return pipeline_name in self._pipeline_index_map

    def get_pipeline_indices(self):
        return self._pipeline_index_map.values()

    @staticmethod
    def from_repository_def(repository_definition):
        return RepositoryIndex(active_repository_data_from_def(repository_definition))


@whitelist_for_serdes
class ActiveRepositoryData(
    namedtuple('_ActiveRepositoryData', 'name pipeline_snapshots active_pipelines')
):
    def __new__(cls, name, pipeline_snapshots, active_pipelines):
        return super(ActiveRepositoryData, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            pipeline_snapshots=check.list_param(
                pipeline_snapshots, 'pipeline_snapshots', of_type=PipelineSnapshot
            ),
            active_pipelines=check.list_param(
                active_pipelines, 'active_pipelines', of_type=ActivePipelineData
            ),
        )

    def get_pipeline_snapshot(self, name):
        check.str_param(name, 'name')

        for pipeline_snapshot in self.pipeline_snapshots:
            if pipeline_snapshot.name == name:
                return pipeline_snapshot

        check.failed('Could not find pipeline snapshot named ' + name)


@whitelist_for_serdes
class ActivePipelineData(namedtuple('_ActivePipelineData', 'name active_presets')):
    def __new__(cls, name, active_presets):
        return super(ActivePipelineData, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            active_presets=check.list_param(
                active_presets, 'active_presets', of_type=ActivePresetData
            ),
        )


@whitelist_for_serdes
class ActivePresetData(namedtuple('_ActivePresetData', 'name environment_dict solid_subset mode')):
    def __new__(cls, name, environment_dict, solid_subset, mode):
        return super(ActivePresetData, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            environment_dict=check.dict_param(environment_dict, 'environment_dict'),
            solid_subset=check.list_param(solid_subset, 'solid_subset', of_type=str)
            if solid_subset is not None
            else None,
            mode=check.str_param(mode, 'mode'),
        )


def active_repository_data_from_def(repository_def):
    check.inst_param(repository_def, 'repository_def', RepositoryDefinition)

    return ActiveRepositoryData(
        name=repository_def.name,
        pipeline_snapshots=sorted(
            [
                PipelineSnapshot.from_pipeline_def(pipeline_definition)
                for pipeline_definition in repository_def.get_all_pipelines()
            ],
            key=lambda ps: ps.name,
        ),
        active_pipelines=sorted(
            list(map(active_pipeline_from_def, repository_def.get_all_pipelines())),
            key=lambda pd: pd.name,
        ),
    )


def active_pipeline_from_def(pipeline_def):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    return ActivePipelineData(
        name=pipeline_def.name,
        active_presets=sorted(
            list(map(active_preset_data_from_def, pipeline_def.preset_defs)), key=lambda pd: pd.name
        ),
    )


def active_preset_data_from_def(preset_def):
    check.inst_param(preset_def, 'preset_def', PresetDefinition)
    return ActivePresetData(
        name=preset_def.name,
        environment_dict=preset_def.environment_dict,
        solid_subset=preset_def.solid_subset,
        mode=preset_def.mode,
    )
