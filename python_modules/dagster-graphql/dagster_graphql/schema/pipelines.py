from __future__ import absolute_import

from dagster_graphql import dauphin

from dagster import (
    LoggerDefinition,
    ModeDefinition,
    PipelineDefinition,
    PresetDefinition,
    ResourceDefinition,
    check,
)
from dagster.core.definitions.pipeline import PipelineRunsFilter
from dagster.seven import lru_cache

from .config_types import to_dauphin_config_type
from .runtime_types import to_dauphin_runtime_type
from .solids import DauphinSolidContainer, build_dauphin_solid_handles, build_dauphin_solids


class DauphinPipelineReference(dauphin.Interface):
    '''This interface supports the case where we can look up a pipeline successfully in the
    repository available to the DagsterInstance/graphql context, as well as the case where we know
    that a pipeline exists/existed thanks to materialized data such as logs and run metadata, but
    where we can't look the concrete pipeline up.'''

    class Meta(object):
        name = 'PipelineReference'

    name = dauphin.NonNull(dauphin.String)


class DauphinUnknownPipeline(dauphin.ObjectType):
    class Meta(object):
        name = 'UnknownPipeline'
        interfaces = (DauphinPipelineReference,)

    name = dauphin.NonNull(dauphin.String)


class DauphinPipeline(dauphin.ObjectType):
    class Meta(object):
        name = 'Pipeline'
        interfaces = (DauphinSolidContainer, DauphinPipelineReference)

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    solids = dauphin.non_null_list('Solid')
    runtime_types = dauphin.non_null_list('RuntimeType')
    runs = dauphin.non_null_list('PipelineRun')
    modes = dauphin.non_null_list('Mode')
    solid_handles = dauphin.Field(
        dauphin.non_null_list('SolidHandle'), parentHandleID=dauphin.String()
    )
    presets = dauphin.non_null_list('PipelinePreset')
    solid_handle = dauphin.Field(
        'SolidHandle', handleID=dauphin.Argument(dauphin.NonNull(dauphin.String)),
    )

    def __init__(self, pipeline):
        super(DauphinPipeline, self).__init__(name=pipeline.name, description=pipeline.description)
        self._pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)

    def resolve_solids(self, _graphene_info):
        return build_dauphin_solids(self._pipeline)

    def resolve_runtime_types(self, _graphene_info):
        return sorted(
            list(
                map(
                    to_dauphin_runtime_type,
                    [t for t in self._pipeline.all_runtime_types() if t.name],
                )
            ),
            key=lambda config_type: config_type.name,
        )

    def resolve_runs(self, graphene_info):
        return [
            graphene_info.schema.type_named('PipelineRun')(r)
            for r in graphene_info.context.instance.get_runs(
                filters=PipelineRunsFilter(pipeline_name=self._pipeline.name)
            )
        ]

    def get_dagster_pipeline(self):
        return self._pipeline

    def get_type(self, _graphene_info, typeName):
        if self._pipeline.has_config_type(typeName):
            return to_dauphin_config_type(self._pipeline.config_type_named(typeName))
        elif self._pipeline.has_runtime_type(typeName):
            return to_dauphin_runtime_type(self._pipeline.runtime_type_named(typeName))

        else:
            check.failed('Not a config type or runtime type')

    def resolve_modes(self, graphene_info):
        return [
            graphene_info.schema.type_named('Mode')(mode_definition)
            for mode_definition in sorted(
                self._pipeline.mode_definitions, key=lambda item: item.name
            )
        ]

    def resolve_solid_handle(self, _graphene_info, handleID):
        return _get_solid_handles(self._pipeline).get(handleID)

    def resolve_solid_handles(self, _graphene_info, **kwargs):
        handles = _get_solid_handles(self._pipeline)
        parentHandleID = kwargs.get('parentHandleID')

        if parentHandleID == "":
            handles = {key: handle for key, handle in handles.items() if not handle.parent}
        elif parentHandleID is not None:
            handles = {
                key: handle
                for key, handle in handles.items()
                if handle.parent and handle.parent.handleID.to_string() == parentHandleID
            }

        return [handles[key] for key in sorted(handles)]

    def resolve_presets(self, _graphene_info):
        return [
            DauphinPipelinePreset(preset, self._pipeline.name)
            for preset in sorted(self._pipeline.get_presets(), key=lambda item: item.name)
        ]


@lru_cache(maxsize=32)
def _get_solid_handles(pipeline):
    return {str(item.handleID): item for item in build_dauphin_solid_handles(pipeline)}


class DauphinPipelineConnection(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineConnection'

    nodes = dauphin.non_null_list('Pipeline')


class DauphinResource(dauphin.ObjectType):
    class Meta(object):
        name = 'Resource'

    def __init__(self, resource_name, resource):
        self.name = check.str_param(resource_name, 'resource_name')
        self._resource = check.inst_param(resource, 'resource', ResourceDefinition)
        self.description = resource.description

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    configField = dauphin.Field('ConfigTypeField')

    def resolve_configField(self, graphene_info):
        return (
            graphene_info.schema.type_named('ConfigTypeField')(
                name="config", field=self._resource.config_field
            )
            if self._resource.config_field
            else None
        )


class DauphinLogger(dauphin.ObjectType):
    class Meta(object):
        name = 'Logger'

    def __init__(self, logger_name, logger):
        self.name = check.str_param(logger_name, 'logger_name')
        self._logger = check.inst_param(logger, 'logger', LoggerDefinition)
        self.description = logger.description

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    configField = dauphin.Field('ConfigTypeField')

    def resolve_configField(self, graphene_info):
        return (
            graphene_info.schema.type_named('ConfigTypeField')(
                name="config", field=self._logger.config_field
            )
            if self._logger.config_field
            else None
        )


class DauphinMode(dauphin.ObjectType):
    def __init__(self, mode_definition):
        self._mode_definition = check.inst_param(mode_definition, 'mode_definition', ModeDefinition)

    class Meta(object):
        name = 'Mode'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    resources = dauphin.non_null_list('Resource')
    loggers = dauphin.non_null_list('Logger')

    def resolve_name(self, _graphene_info):
        return self._mode_definition.name

    def resolve_description(self, _graphene_info):
        return self._mode_definition.description

    def resolve_resources(self, _graphene_info):
        return [
            DauphinResource(*item) for item in sorted(self._mode_definition.resource_defs.items())
        ]

    def resolve_loggers(self, _graphene_info):
        return [DauphinLogger(*item) for item in sorted(self._mode_definition.loggers.items())]


class DauphinMetadataItemDefinition(dauphin.ObjectType):
    class Meta(object):
        name = 'MetadataItemDefinition'

    key = dauphin.NonNull(dauphin.String)
    value = dauphin.NonNull(dauphin.String)


class DauphinPipelinePreset(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelinePreset'

    name = dauphin.NonNull(dauphin.String)
    solidSubset = dauphin.List(dauphin.NonNull(dauphin.String))
    environmentConfigYaml = dauphin.NonNull(dauphin.String)
    mode = dauphin.NonNull(dauphin.String)

    def __init__(self, preset, pipeline_name):
        self._preset = check.inst_param(preset, 'preset', PresetDefinition)
        self._pipeline_name = check.str_param(pipeline_name, 'pipeline_name')

    def resolve_name(self, _graphene_info):
        return self._preset.name

    def resolve_solidSubset(self, _graphene_info):
        return self._preset.solid_subset

    def resolve_environmentConfigYaml(self, _graphene_info):
        yaml = self._preset.get_environment_yaml()
        return yaml if yaml else ''

    def resolve_mode(self, _graphene_info):
        return self._preset.mode
