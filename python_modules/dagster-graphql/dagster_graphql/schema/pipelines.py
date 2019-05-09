from __future__ import absolute_import

from dagster import (
    ExpectationDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    ResourceDefinition,
    check,
)
from dagster.core.definitions import (
    ISolidDefinition,
    PipelinePreset,
    Solid,
    SolidInputHandle,
    SolidOutputHandle,
    create_environment_schema,
    create_environment_type,
)
from dagster_graphql import dauphin

from .config_types import to_dauphin_config_type
from .runtime_types import to_dauphin_runtime_type


class DauphinPipeline(dauphin.ObjectType):
    class Meta:
        name = 'Pipeline'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    solids = dauphin.non_null_list('Solid')
    contexts = dauphin.non_null_list('PipelineContext')
    environment_type = dauphin.NonNull('ConfigType')
    config_types = dauphin.non_null_list('ConfigType')
    runtime_types = dauphin.non_null_list('RuntimeType')
    runs = dauphin.non_null_list('PipelineRun')

    def __init__(self, pipeline):
        super(DauphinPipeline, self).__init__(name=pipeline.name, description=pipeline.description)
        self._pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)

    def resolve_solids(self, graphene_info):
        return [
            graphene_info.schema.type_named('Solid')(
                solid,
                self._pipeline.dependency_structure.deps_of_solid_with_input(solid.name),
                self._pipeline.dependency_structure.depended_by_of_solid(solid.name),
            )
            for solid in self._pipeline.solids
        ]

    def resolve_contexts(self, graphene_info):
        return [
            graphene_info.schema.type_named('PipelineContext')(name=name, context=context)
            for name, context in self._pipeline.context_definitions.items()
        ]

    def resolve_environment_type(self, _graphene_info):
        return to_dauphin_config_type(create_environment_type(self._pipeline))

    def resolve_config_types(self, _graphene_info):
        environment_schema = create_environment_schema(self._pipeline)
        return sorted(
            list(map(to_dauphin_config_type, environment_schema.all_config_types())),
            key=lambda config_type: config_type.key,
        )

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
            for r in graphene_info.context.pipeline_runs.all_runs_for_pipeline(self._pipeline.name)
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


class DauphinPipelineConnection(dauphin.ObjectType):
    class Meta:
        name = 'PipelineConnection'

    nodes = dauphin.non_null_list('Pipeline')


class DauphinResource(dauphin.ObjectType):
    class Meta:
        name = 'Resource'

    def __init__(self, resource_name, resource):
        self.name = check.str_param(resource_name, 'resource_name')
        self._resource = check.inst_param(resource, 'resource', ResourceDefinition)
        self.description = resource.description

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    config = dauphin.Field('ConfigTypeField')

    def resolve_config(self, graphene_info):
        return (
            graphene_info.schema.type_named('ConfigTypeField')(
                name="config", field=self._resource.config_field
            )
            if self._resource.config_field
            else None
        )


class DauphinPipelineContext(dauphin.ObjectType):
    class Meta:
        name = 'PipelineContext'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    config = dauphin.Field('ConfigTypeField')
    resources = dauphin.non_null_list('Resource')

    def __init__(self, name, context):
        super(DauphinPipelineContext, self).__init__(name=name, description=context.description)
        self._context = check.inst_param(context, 'context', PipelineContextDefinition)

    def resolve_config(self, graphene_info):
        return (
            graphene_info.schema.type_named('ConfigTypeField')(
                name="config", field=self._context.config_field
            )
            if self._context.config_field
            else None
        )

    def resolve_resources(self, _graphene_info):
        return [DauphinResource(*item) for item in self._context.resource_defs.items()]


class DauphinSolid(dauphin.ObjectType):
    class Meta:
        name = 'Solid'

    name = dauphin.NonNull(dauphin.String)
    definition = dauphin.NonNull('SolidDefinition')
    inputs = dauphin.non_null_list('Input')
    outputs = dauphin.non_null_list('Output')

    def __init__(self, solid, depends_on=None, depended_by=None):
        super(DauphinSolid, self).__init__(name=solid.name)

        self._solid = check.inst_param(solid, 'solid', Solid)

        if depends_on:
            self.depends_on = {
                input_handle: output_handle for input_handle, output_handle in depends_on.items()
            }
        else:
            self.depends_on = {}

        if depended_by:
            self.depended_by = {
                output_handle: input_handles for output_handle, input_handles in depended_by.items()
            }
        else:
            self.depended_by = {}

    def resolve_definition(self, graphene_info):
        return graphene_info.schema.type_named('SolidDefinition')(self._solid.definition)

    def resolve_inputs(self, graphene_info):
        return [
            graphene_info.schema.type_named('Input')(input_handle, self)
            for input_handle in self._solid.input_handles()
        ]

    def resolve_outputs(self, graphene_info):
        return [
            graphene_info.schema.type_named('Output')(output_handle, self)
            for output_handle in self._solid.output_handles()
        ]


class DauphinInput(dauphin.ObjectType):
    class Meta:
        name = 'Input'

    solid = dauphin.NonNull('Solid')
    definition = dauphin.NonNull('InputDefinition')
    depends_on = dauphin.Field('Output')

    def __init__(self, input_handle, solid):
        super(DauphinInput, self).__init__(solid=solid)
        self._solid = check.inst_param(solid, 'solid', DauphinSolid)
        self._input_handle = check.inst_param(input_handle, 'input_handle', SolidInputHandle)

    def resolve_definition(self, graphene_info):
        return graphene_info.schema.type_named('InputDefinition')(
            self._input_handle.input_def, self._solid.resolve_definition(graphene_info)
        )

    def resolve_depends_on(self, graphene_info):
        if self._input_handle in self._solid.depends_on:
            return graphene_info.schema.type_named('Output')(
                self._solid.depends_on[self._input_handle],
                graphene_info.schema.type_named('Solid')(
                    self._solid.depends_on[self._input_handle].solid
                ),
            )
        else:
            return None


class DauphinOutput(dauphin.ObjectType):
    class Meta:
        name = 'Output'

    solid = dauphin.NonNull('Solid')
    definition = dauphin.NonNull('OutputDefinition')
    depended_by = dauphin.non_null_list('Input')

    def __init__(self, output_handle, solid):
        super(DauphinOutput, self).__init__(solid=solid)
        self._solid = check.inst_param(solid, 'solid', DauphinSolid)
        self._output_handle = check.inst_param(output_handle, 'output_handle', SolidOutputHandle)

    def resolve_definition(self, graphene_info):
        return graphene_info.schema.type_named('OutputDefinition')(
            self._output_handle.output_def, self._solid.resolve_definition(graphene_info)
        )

    def resolve_depended_by(self, graphene_info):
        return [
            graphene_info.schema.type_named('Input')(input_handle, DauphinSolid(input_handle.solid))
            for input_handle in self._solid.depended_by.get(self._output_handle, [])
        ]


class DauphinMetadataItemDefinition(dauphin.ObjectType):
    class Meta:
        name = 'MetadataItemDefinition'

    key = dauphin.NonNull(dauphin.String)
    value = dauphin.NonNull(dauphin.String)


class DauphinSolidDefinition(dauphin.ObjectType):
    class Meta:
        name = 'SolidDefinition'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    metadata = dauphin.non_null_list('MetadataItemDefinition')
    input_definitions = dauphin.non_null_list('InputDefinition')
    output_definitions = dauphin.non_null_list('OutputDefinition')
    config_definition = dauphin.Field('ConfigTypeField')

    # solids - ?

    def __init__(self, solid_def):
        super(DauphinSolidDefinition, self).__init__(
            name=solid_def.name, description=solid_def.description
        )

        self._solid_def = check.inst_param(solid_def, 'solid_def', ISolidDefinition)

    def resolve_metadata(self, graphene_info):
        return [
            graphene_info.schema.type_named('MetadataItemDefinition')(key=item[0], value=item[1])
            for item in self._solid_def.metadata.items()
        ]

    def resolve_input_definitions(self, graphene_info):
        return [
            graphene_info.schema.type_named('InputDefinition')(input_definition, self)
            for input_definition in self._solid_def.input_defs
        ]

    def resolve_output_definitions(self, graphene_info):
        return [
            graphene_info.schema.type_named('OutputDefinition')(output_definition, self)
            for output_definition in self._solid_def.output_defs
        ]

    def resolve_config_definition(self, graphene_info):
        return (
            graphene_info.schema.type_named('ConfigTypeField')(
                name="config", field=self._solid_def.config_field
            )
            if self._solid_def.config_field
            else None
        )


class DauphinInputDefinition(dauphin.ObjectType):
    class Meta:
        name = 'InputDefinition'

    solid_definition = dauphin.NonNull('SolidDefinition')
    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    type = dauphin.NonNull('RuntimeType')
    expectations = dauphin.non_null_list('Expectation')

    # inputs - ?

    def __init__(self, input_definition, solid_def):
        super(DauphinInputDefinition, self).__init__(
            name=input_definition.name,
            description=input_definition.description,
            solid_definition=solid_def,
        )
        self._input_definition = check.inst_param(
            input_definition, 'input_definition', InputDefinition
        )

    def resolve_type(self, _graphene_info):
        return to_dauphin_runtime_type(self._input_definition.runtime_type)

    def resolve_expectations(self, graphene_info):
        if self._input_definition.expectations:
            return [
                graphene_info.schema.type_named('Expectation')(expectation)
                for expectation in self._input_definition.expectations
            ]
        else:
            return []


class DauphinOutputDefinition(dauphin.ObjectType):
    class Meta:
        name = 'OutputDefinition'

    solid_definition = dauphin.NonNull('SolidDefinition')
    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    type = dauphin.NonNull('RuntimeType')
    expectations = dauphin.non_null_list('Expectation')

    # outputs - ?

    def __init__(self, output_definition, solid_def):
        super(DauphinOutputDefinition, self).__init__(
            name=output_definition.name,
            description=output_definition.description,
            solid_definition=solid_def,
        )
        self._output_definition = check.inst_param(
            output_definition, 'output_definition', OutputDefinition
        )

    def resolve_type(self, _graphene_info):
        return to_dauphin_runtime_type(self._output_definition.runtime_type)

    def resolve_expectations(self, graphene_info):
        if self._output_definition.expectations:
            return [
                graphene_info.schema.type_named('Expectation')(expectation)
                for expectation in self._output_definition.expectations
            ]
        else:
            return []


class DauphinExpectation(dauphin.ObjectType):
    class Meta:
        name = 'Expectation'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()

    def __init__(self, expectation):
        check.inst_param(expectation, 'expectation', ExpectationDefinition)
        super(DauphinExpectation, self).__init__(
            name=expectation.name, description=expectation.description
        )


class DauphinPipelinePreset(dauphin.ObjectType):
    class Meta:
        name = 'PipelinePreset'

    name = dauphin.NonNull(dauphin.String)
    solidSubset = dauphin.List(dauphin.NonNull(dauphin.String))
    environment = dauphin.String()

    def __init__(self, preset):
        self.preset = check.inst_param(preset, 'preset', PipelinePreset)

    def resolve_name(self, _graphene_info):
        return self.preset.name

    def resolve_solidSubset(self, _graphene_info):
        return self.preset.solid_subset

    def resolve_environment(self, _graphene_info):
        return self.preset.environment_yaml
