'''
This module contains data objects meant to be serialized between
host processes and user processes. They should contain no
business logic or clever indexing. Use the classes in external.py
for that.
'''

from collections import namedtuple

from dagster import check
from dagster.core.definitions import PipelineDefinition, PresetDefinition, RepositoryDefinition
from dagster.core.snap import PipelineSnapshot
from dagster.serdes import whitelist_for_serdes


@whitelist_for_serdes
class ActiveRepositoryData(namedtuple('_ActiveRepositoryData', 'name active_pipeline_datas')):
    def __new__(cls, name, active_pipeline_datas):
        return super(ActiveRepositoryData, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            active_pipeline_datas=check.list_param(
                active_pipeline_datas, 'active_pipeline_datas', of_type=ActivePipelineData
            ),
        )

    def get_pipeline_snapshot(self, name):
        check.str_param(name, 'name')

        for active_pipeline_data in self.active_pipeline_datas:
            if active_pipeline_data.name == name:
                return active_pipeline_data.pipeline_snapshot

        check.failed('Could not find pipeline snapshot named ' + name)

    def get_active_pipeline_data(self, name):
        check.str_param(name, 'name')

        for active_pipeline in self.active_pipeline_datas:
            if active_pipeline.name == name:
                return active_pipeline

        check.failed('Could not find active pipeline data named ' + name)


@whitelist_for_serdes
class ActivePipelineData(
    namedtuple('_ActivePipelineData', 'name pipeline_snapshot active_presets')
):
    def __new__(cls, name, pipeline_snapshot, active_presets):
        return super(ActivePipelineData, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            pipeline_snapshot=check.inst_param(
                pipeline_snapshot, 'pipeline_snapshot', PipelineSnapshot
            ),
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
            environment_dict=check.opt_dict_param(environment_dict, 'environment_dict'),
            solid_subset=check.list_param(solid_subset, 'solid_subset', of_type=str)
            if solid_subset is not None
            else None,
            mode=check.str_param(mode, 'mode'),
        )


def active_repository_data_from_def(repository_def):
    check.inst_param(repository_def, 'repository_def', RepositoryDefinition)

    return ActiveRepositoryData(
        name=repository_def.name,
        active_pipeline_datas=sorted(
            list(map(active_pipeline_data_from_def, repository_def.get_all_pipelines())),
            key=lambda pd: pd.name,
        ),
    )


def active_pipeline_data_from_def(pipeline_def):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    return ActivePipelineData(
        name=pipeline_def.name,
        pipeline_snapshot=PipelineSnapshot.from_pipeline_def(pipeline_def),
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
