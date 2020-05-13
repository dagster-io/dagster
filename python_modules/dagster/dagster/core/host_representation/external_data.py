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
class ExternalRepositoryData(namedtuple('_ExternalRepositoryData', 'name external_pipeline_datas')):
    def __new__(cls, name, external_pipeline_datas):
        return super(ExternalRepositoryData, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            external_pipeline_datas=check.list_param(
                external_pipeline_datas, 'external_pipeline_datas', of_type=ExternalPipelineData
            ),
        )

    def get_pipeline_snapshot(self, name):
        check.str_param(name, 'name')

        for external_pipeline_data in self.external_pipeline_datas:
            if external_pipeline_data.name == name:
                return external_pipeline_data.pipeline_snapshot

        check.failed('Could not find pipeline snapshot named ' + name)

    def get_external_pipeline_data(self, name):
        check.str_param(name, 'name')

        for external_pipeline_data in self.external_pipeline_datas:
            if external_pipeline_data.name == name:
                return external_pipeline_data

        check.failed('Could not find active pipeline data named ' + name)


@whitelist_for_serdes
class ExternalPipelineData(
    namedtuple('_ExternalPipelineData', 'name pipeline_snapshot active_presets')
):
    def __new__(cls, name, pipeline_snapshot, active_presets):
        return super(ExternalPipelineData, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            pipeline_snapshot=check.inst_param(
                pipeline_snapshot, 'pipeline_snapshot', PipelineSnapshot
            ),
            active_presets=check.list_param(
                active_presets, 'active_presets', of_type=ExternalPresetData
            ),
        )


@whitelist_for_serdes
class ExternalPresetData(
    namedtuple('_ExternalPresetData', 'name environment_dict solid_subset mode')
):
    def __new__(cls, name, environment_dict, solid_subset, mode):
        return super(ExternalPresetData, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            environment_dict=check.opt_dict_param(environment_dict, 'environment_dict'),
            solid_subset=check.list_param(solid_subset, 'solid_subset', of_type=str)
            if solid_subset is not None
            else None,
            mode=check.str_param(mode, 'mode'),
        )


def external_repository_data_from_def(repository_def):
    check.inst_param(repository_def, 'repository_def', RepositoryDefinition)

    return ExternalRepositoryData(
        name=repository_def.name,
        external_pipeline_datas=sorted(
            list(map(external_pipeline_data_from_def, repository_def.get_all_pipelines())),
            key=lambda pd: pd.name,
        ),
    )


def external_pipeline_data_from_def(pipeline_def):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    return ExternalPipelineData(
        name=pipeline_def.name,
        pipeline_snapshot=PipelineSnapshot.from_pipeline_def(pipeline_def),
        active_presets=sorted(
            list(map(external_preset_data_from_def, pipeline_def.preset_defs)),
            key=lambda pd: pd.name,
        ),
    )


def external_preset_data_from_def(preset_def):
    check.inst_param(preset_def, 'preset_def', PresetDefinition)
    return ExternalPresetData(
        name=preset_def.name,
        environment_dict=preset_def.environment_dict,
        solid_subset=preset_def.solid_subset,
        mode=preset_def.mode,
    )
