from __future__ import absolute_import

import dagster
from dagster.core.types import DagsterCompositeTypeBase
from dagster import (
    InputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    SolidDefinition,
    check,
)
from dagster.core.definitions import (
    Solid,
    SolidInputHandle,
    SolidOutputHandle,
)

from dagit.schema import dauphin


class DauphinPipeline(dauphin.ObjectType):
    class Meta:
        name = 'Pipeline'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    solids = dauphin.non_null_list('Solid')
    contexts = dauphin.non_null_list('PipelineContext')
    environment_type = dauphin.NonNull('Type')
    types = dauphin.non_null_list('Type')
    runs = dauphin.non_null_list('PipelineRun')

    def __init__(self, pipeline):
        super(DauphinPipeline, self).__init__(name=pipeline.name, description=pipeline.description)
        self._pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)

    def resolve_solids(self, info):
        return [
            info.schema.Solid(
                solid,
                self._pipeline.dependency_structure.deps_of_solid_with_input(solid.name),
                self._pipeline.dependency_structure.depended_by_of_solid(solid.name),
            ) for solid in self._pipeline.solids
        ]

    def resolve_contexts(self, info):
        return [
            info.schema.PipelineContext(name=name, context=context)
            for name, context in self._pipeline.context_definitions.items()
        ]

    def resolve_environment_type(self, info):
        return info.schema.Type.from_dagster_type(info, self._pipeline.environment_type)

    def resolve_types(self, info):
        return sorted(
            [
                info.schema.Type.from_dagster_type(info, type_)
                for type_ in self._pipeline.all_types()
            ],
            key=lambda type_: type_.name
        )

    def resolve_runs(self, info):
        return [
            info.schema.PipelineRun(r)
            for r in info.context.pipeline_runs.all_runs_for_pipeline(self._pipeline.name)
        ]

    def get_dagster_pipeline(self):
        return self._pipeline

    def get_type(self, info, typeName):
        return info.schema.Type.from_dagster_type(info, self._pipeline.type_named(typeName))


class DauphinPipelineConnection(dauphin.ObjectType):
    class Meta:
        name = 'PipelineConnection'

    nodes = dauphin.non_null_list('Pipeline')


class DauphinPipelineContext(dauphin.ObjectType):
    class Meta:
        name = 'PipelineContext'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    config = dauphin.Field('Config')

    def __init__(self, name, context):
        super(DauphinPipelineContext, self).__init__(name=name, description=context.description)
        self._context = check.inst_param(context, 'context', PipelineContextDefinition)

    def resolve_config(self, info):
        return info.schema.Config(
            self._context.config_field
        ) if self._context.config_field else None


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
                input_handle: output_handle
                for input_handle, output_handle in depends_on.items()
            }
        else:
            self.depends_on = {}

        if depended_by:
            self.depended_by = {
                output_handle: input_handles
                for output_handle, input_handles in depended_by.items()
            }
        else:
            self.depended_by = {}

    def resolve_definition(self, info):
        return info.schema.SolidDefinition(self._solid.definition)

    def resolve_inputs(self, info):
        return [
            info.schema.Input(input_handle, self) for input_handle in self._solid.input_handles()
        ]

    def resolve_outputs(self, info):
        return [
            info.schema.Output(output_handle, self)
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

    def resolve_definition(self, info):
        return info.schema.InputDefinition(
            self._input_handle.input_def, self._solid.resolve_definition(info)
        )

    def resolve_depends_on(self, info):
        if self._input_handle in self._solid.depends_on:
            return info.schema.Output(
                self._solid.depends_on[self._input_handle],
                info.schema.Solid(self._solid.depends_on[self._input_handle].solid),
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

    def resolve_definition(self, info):
        return info.schema.OutputDefinition(
            self._output_handle.output_def, self._solid.resolve_definition(info)
        )

    def resolve_depended_by(self, info):
        return [
            info.schema.Input(
                input_handle,
                DauphinSolid(input_handle.solid),
            ) for input_handle in self._solid.depended_by.get(self._output_handle, [])
        ]


class DauphinSolidMetadataItemDefinition(dauphin.ObjectType):
    class Meta:
        name = 'SolidMetadataItemDefinition'

    key = dauphin.NonNull(dauphin.String)
    value = dauphin.NonNull(dauphin.String)


class DauphinSolidDefinition(dauphin.ObjectType):
    class Meta:
        name = 'SolidDefinition'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    metadata = dauphin.non_null_list('SolidMetadataItemDefinition')
    input_definitions = dauphin.non_null_list('InputDefinition')
    output_definitions = dauphin.non_null_list('OutputDefinition')
    config_definition = dauphin.Field('Config')

    # solids - ?

    def __init__(self, solid_def):
        super(DauphinSolidDefinition, self).__init__(
            name=solid_def.name,
            description=solid_def.description,
        )

        self._solid_def = check.inst_param(solid_def, 'solid_def', SolidDefinition)

    def resolve_metadata(self, info):
        return [
            info.schema.SolidMetadataItemDefinition(key=item[0], value=item[1])
            for item in self._solid_def.metadata.items()
        ]

    def resolve_input_definitions(self, info):
        return [
            info.schema.InputDefinition(input_definition, self)
            for input_definition in self._solid_def.input_defs
        ]

    def resolve_output_definitions(self, info):
        return [
            info.schema.OutputDefinition(output_definition, self)
            for output_definition in self._solid_def.output_defs
        ]

    def resolve_config_definition(self, info):
        return info.schema.Config(
            self._solid_def.config_field
        ) if self._solid_def.config_field else None


class DauphinInputDefinition(dauphin.ObjectType):
    class Meta:
        name = 'InputDefinition'

    solid_definition = dauphin.NonNull('SolidDefinition')
    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    type = dauphin.NonNull('Type')
    expectations = dauphin.non_null_list('Expectation')

    # inputs - ?

    def __init__(self, input_definition, solid_def):
        super(DauphinInputDefinition, self).__init__(
            name=input_definition.name,
            description=input_definition.description,
            solid_definition=solid_def,
        )
        self._input_definition = check.inst_param(
            input_definition,
            'input_definition',
            InputDefinition,
        )

    def resolve_type(self, info):
        return info.schema.Type.from_dagster_type(
            info,
            dagster_type=self._input_definition.dagster_type,
        )

    def resolve_expectations(self, info):
        if self._input_definition.expectations:
            return [
                info.schema.Expectation(
                    expectation for expectation in self._input_definition.expectations
                )
            ]
        else:
            return []


class OutputDefinition(dauphin.ObjectType):
    solid_definition = dauphin.NonNull('SolidDefinition')
    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    type = dauphin.NonNull('Type')
    expectations = dauphin.non_null_list('Expectation')

    # outputs - ?

    def __init__(self, output_definition, solid_def):
        super(OutputDefinition, self).__init__(
            name=output_definition.name,
            description=output_definition.description,
            solid_definition=solid_def,
        )
        self._output_definition = check.inst_param(
            output_definition, 'output_definition', dagster.OutputDefinition
        )

    def resolve_type(self, info):
        return info.schema.Type.from_dagster_type(
            info, dagster_type=self._output_definition.dagster_type
        )

    def resolve_expectations(self, info):
        if self._output_definition.expectations:
            return [
                info.schema.Expectation(expectation)
                for expectation in self._output_definition.expectations
            ]
        else:
            return []


class Expectation(dauphin.ObjectType):
    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()

    def __init__(self, expectation):
        check.inst_param(expectation, 'expectation', dagster.ExpectationDefinition)
        super(Expectation, self).__init__(
            name=expectation.name, description=expectation.description
        )


class Config(dauphin.ObjectType):
    type = dauphin.NonNull('Type')

    def __init__(self, config_field):
        super(Config, self).__init__()
        self._config_field = check.opt_inst_param(config_field, 'config_field', dagster.Field)

    def resolve_type(self, info):
        return info.schema.Type.from_dagster_type(
            info, dagster_type=self._config_field.dagster_type
        )


class TypeAttributes(dauphin.ObjectType):
    is_builtin = dauphin.NonNull(
        dauphin.Boolean,
        description='''
True if the system defines it and it is the same type across pipelines.
Examples include "Int" and "String."''',
    )
    is_system_config = dauphin.NonNull(
        dauphin.Boolean,
        description='''
Dagster generates types for base elements of the config system (e.g. the solids and
context field of the base environment). These types are always present
and are typically not relevant to an end user. This flag allows tool authors to
filter out those types by default.
''',
    )

    is_named = dauphin.NonNull(dauphin.Boolean)


class Type(dauphin.Interface):
    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    type_attributes = dauphin.NonNull('TypeAttributes')

    @classmethod
    def from_dagster_type(cls, info, dagster_type):
        if isinstance(dagster_type, DagsterCompositeTypeBase):
            return info.schema.CompositeType(dagster_type)
        else:
            return info.schema.RegularType(dagster_type)


class RegularType(dauphin.ObjectType):
    class Meta:
        interfaces = [
            Type,
        ]

    def __init__(self, dagster_type):
        super(RegularType, self).__init__(
            name=dagster_type.name,
            description=dagster_type.description,
        )
        self._dagster_type = dagster_type

    def resolve_type_attributes(self, _info):
        return self._dagster_type.type_attributes


class CompositeType(dauphin.ObjectType):
    fields = dauphin.non_null_list('TypeField')

    class Meta:
        interfaces = [
            Type,
        ]

    def __init__(self, dagster_type):
        super(CompositeType, self).__init__(
            name=dagster_type.name,
            description=dagster_type.description,
        )
        self._dagster_type = dagster_type

    def resolve_type_attributes(self, info):
        return info.schema.TypeAttributes(*self._dagster_type.type_attributes)

    def resolve_fields(self, info):
        return [
            info.schema.TypeField(name=k, field=v) for k, v in self._dagster_type.field_dict.items()
        ]


class TypeField(dauphin.ObjectType):
    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    type = dauphin.NonNull('Type')
    default_value = dauphin.String()
    is_optional = dauphin.NonNull(dauphin.Boolean)

    def __init__(self, name, field):
        super(TypeField, self).__init__(
            name=name,
            description=field.description,
            default_value=field.default_value_as_str if field.default_provided else None,
            is_optional=field.is_optional
        )
        self._field = field

    def resolve_type(self, info):
        return info.schema.Type.from_dagster_type(info, dagster_type=self._field.dagster_type)
