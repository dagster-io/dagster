from __future__ import absolute_import

from dagster import (
    ExpectationDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    ResourceDefinition,
    SolidDefinition,
    check,
)

from dagster.core.definitions import Solid, SolidInputHandle, SolidOutputHandle
from dagster.core.types.runtime import RuntimeType
from dagster.core.types.config import ConfigType, DEFAULT_TYPE_ATTRIBUTES

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
            info.schema.type_named('Solid')(
                solid,
                self._pipeline.dependency_structure.deps_of_solid_with_input(solid.name),
                self._pipeline.dependency_structure.depended_by_of_solid(solid.name),
            )
            for solid in self._pipeline.solids
        ]

    def resolve_contexts(self, info):
        return [
            info.schema.type_named('PipelineContext')(name=name, context=context)
            for name, context in self._pipeline.context_definitions.items()
        ]

    def resolve_environment_type(self, info):
        return info.schema.type_named('Type').to_dauphin_type(info, self._pipeline.environment_type)

    def resolve_types(self, info):
        return sorted(
            [
                info.schema.type_named('Type').to_dauphin_type(info, type_)
                for type_ in all_types(self._pipeline)
            ],
            key=lambda type_: type_.name,
        )

    def resolve_runs(self, info):
        return [
            info.schema.type_named('PipelineRun')(r)
            for r in info.context.pipeline_runs.all_runs_for_pipeline(self._pipeline.name)
        ]

    def get_dagster_pipeline(self):
        return self._pipeline

    def get_type(self, info, typeName):
        to_dauphin_type = info.schema.type_named('Type').to_dauphin_type
        if self._pipeline.has_config_type(typeName):
            return to_dauphin_type(info, self._pipeline.config_type_named(typeName))
        elif self._pipeline.has_runtime_type(typeName):
            return to_dauphin_type(info, self._pipeline.runtime_type_named(typeName))
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
    config = dauphin.Field('TypeField')

    def resolve_config(self, info):
        return (
            info.schema.type_named('TypeField')(name="config", field=self._resource.config_field)
            if self._resource.config_field
            else None
        )


class DauphinPipelineContext(dauphin.ObjectType):
    class Meta:
        name = 'PipelineContext'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    config = dauphin.Field('TypeField')
    resources = dauphin.non_null_list('Resource')

    def __init__(self, name, context):
        super(DauphinPipelineContext, self).__init__(name=name, description=context.description)
        self._context = check.inst_param(context, 'context', PipelineContextDefinition)

    def resolve_config(self, info):
        return (
            info.schema.type_named('TypeField')(name="config", field=self._context.config_field)
            if self._context.config_field
            else None
        )

    def resolve_resources(self, _info):
        return [DauphinResource(*item) for item in self._context.resources.items()]


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

    def resolve_definition(self, info):
        return info.schema.type_named('SolidDefinition')(self._solid.definition)

    def resolve_inputs(self, info):
        return [
            info.schema.type_named('Input')(input_handle, self)
            for input_handle in self._solid.input_handles()
        ]

    def resolve_outputs(self, info):
        return [
            info.schema.type_named('Output')(output_handle, self)
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
        return info.schema.type_named('InputDefinition')(
            self._input_handle.input_def, self._solid.resolve_definition(info)
        )

    def resolve_depends_on(self, info):
        if self._input_handle in self._solid.depends_on:
            return info.schema.type_named('Output')(
                self._solid.depends_on[self._input_handle],
                info.schema.type_named('Solid')(self._solid.depends_on[self._input_handle].solid),
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
        return info.schema.type_named('OutputDefinition')(
            self._output_handle.output_def, self._solid.resolve_definition(info)
        )

    def resolve_depended_by(self, info):
        return [
            info.schema.type_named('Input')(input_handle, DauphinSolid(input_handle.solid))
            for input_handle in self._solid.depended_by.get(self._output_handle, [])
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
    config_definition = dauphin.Field('TypeField')

    # solids - ?

    def __init__(self, solid_def):
        super(DauphinSolidDefinition, self).__init__(
            name=solid_def.name, description=solid_def.description
        )

        self._solid_def = check.inst_param(solid_def, 'solid_def', SolidDefinition)

    def resolve_metadata(self, info):
        return [
            info.schema.type_named('SolidMetadataItemDefinition')(key=item[0], value=item[1])
            for item in self._solid_def.metadata.items()
        ]

    def resolve_input_definitions(self, info):
        return [
            info.schema.type_named('InputDefinition')(input_definition, self)
            for input_definition in self._solid_def.input_defs
        ]

    def resolve_output_definitions(self, info):
        return [
            info.schema.type_named('OutputDefinition')(output_definition, self)
            for output_definition in self._solid_def.output_defs
        ]

    def resolve_config_definition(self, info):
        return (
            info.schema.type_named('TypeField')(name="config", field=self._solid_def.config_field)
            if self._solid_def.config_field
            else None
        )


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
            input_definition, 'input_definition', InputDefinition
        )

    def resolve_type(self, info):
        return info.schema.type_named('Type').to_dauphin_type(
            info, self._input_definition.runtime_type
        )

    def resolve_expectations(self, info):
        if self._input_definition.expectations:
            return [
                info.schema.type_named('Expectation')(
                    expectation for expectation in self._input_definition.expectations
                )
            ]
        else:
            return []


class DauphinOutputDefinition(dauphin.ObjectType):
    class Meta:
        name = 'OutputDefinition'

    solid_definition = dauphin.NonNull('SolidDefinition')
    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    type = dauphin.NonNull('Type')
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

    def resolve_type(self, info):
        return info.schema.type_named('Type').to_dauphin_type(
            info, self._output_definition.runtime_type
        )

    def resolve_expectations(self, info):
        if self._output_definition.expectations:
            return [
                info.schema.type_named('Expectation')(expectation)
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


class DauphinTypeAttributes(dauphin.ObjectType):
    class Meta:
        name = 'TypeAttributes'

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


class DauphinType(dauphin.Interface):
    class Meta:
        name = 'Type'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    type_attributes = dauphin.NonNull('TypeAttributes')

    is_dict = dauphin.NonNull(dauphin.Boolean)
    is_nullable = dauphin.NonNull(dauphin.Boolean)
    is_list = dauphin.NonNull(dauphin.Boolean)
    is_selector = dauphin.NonNull(dauphin.Boolean)

    inner_types = dauphin.non_null_list('Type')

    @classmethod
    def to_dauphin_type(cls, info, config_or_runtime_type):
        if isinstance(config_or_runtime_type, ConfigType) and config_or_runtime_type.has_fields:
            return info.schema.type_named('CompositeType')(config_or_runtime_type)
        else:
            return info.schema.type_named('RegularType')(config_or_runtime_type)


class DauphinRegularType(dauphin.ObjectType):
    class Meta:
        name = 'RegularType'
        interfaces = [DauphinType]

    def __init__(self, runtime_type):

        super(DauphinRegularType, self).__init__(**ctor_kwargs(runtime_type))
        self._runtime_type = runtime_type

    def resolve_type_attributes(self, _info):
        return type_attributes(self._runtime_type)

    def resolve_inner_types(self, info):
        return inner_types(info, self._runtime_type)


# Section: Type Reconciliation
# These are a temporary set of functions that should be eliminated
# once dagit is aware of the config vs runtime systems and the
# graphql schema updated accordingly
#
# DauphinType.to_dauphin_type also qualifies as a function that is
# aware of the two type systems
#
def all_types(pipeline):
    runtime_types = pipeline.all_runtime_types()

    all_types_dicts = {rt.name: rt for rt in runtime_types}

    for config_type in pipeline.all_config_types():
        all_types_dicts[config_type.name] = config_type
    return list(all_types_dicts.values())


def ctor_kwargs(runtime_type):
    if isinstance(runtime_type, RuntimeType):
        return dict(
            name=runtime_type.name,
            description=runtime_type.description,
            is_dict=False,
            is_selector=False,
            is_nullable=runtime_type.is_nullable,
            is_list=runtime_type.is_list,
        )
    elif isinstance(runtime_type, ConfigType):
        return dict(
            name=runtime_type.name,
            description=runtime_type.description,
            is_dict=check.bool_param(runtime_type.has_fields, 'is_dict'),
            is_selector=runtime_type.is_selector,
            is_nullable=runtime_type.is_nullable,
            is_list=runtime_type.is_list,
        )
    else:
        check.failed('Not a valid type inst')


def type_attributes(runtime_type):
    if isinstance(runtime_type, RuntimeType):
        return DEFAULT_TYPE_ATTRIBUTES
    elif isinstance(runtime_type, ConfigType):
        return runtime_type.type_attributes
    else:
        check.failed('')


def inner_types_of_runtime(info, runtime_type):
    if runtime_type.is_list or runtime_type.is_nullable:
        return [DauphinType.to_dauphin_type(info, runtime_type.inner_type)]
    else:
        return []


def inner_types_of_config(info, config_type):
    return [DauphinType.to_dauphin_type(info, inner_type) for inner_type in config_type.inner_types]


def inner_types(info, runtime_type):
    if isinstance(runtime_type, RuntimeType):
        return inner_types_of_runtime(info, runtime_type)
    elif isinstance(runtime_type, ConfigType):
        return inner_types_of_config(info, runtime_type)
    else:
        check.failed('')


# End Type Reconciliation section


class DauphinCompositeType(dauphin.ObjectType):
    class Meta:
        name = 'CompositeType'
        interfaces = [DauphinType]

    fields = dauphin.non_null_list('TypeField')

    def __init__(self, runtime_type):
        super(DauphinCompositeType, self).__init__(**ctor_kwargs(runtime_type))
        self._runtime_type = runtime_type

    def resolve_inner_types(self, info):
        return inner_types(info, self._runtime_type)

    def resolve_type_attributes(self, _info):
        return type_attributes(self._runtime_type)

    def resolve_fields(self, info):
        return [
            info.schema.type_named('TypeField')(name=k, field=v)
            for k, v in self._runtime_type.fields.items()
        ]


class DauphinTypeField(dauphin.ObjectType):
    class Meta:
        name = 'TypeField'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    type = dauphin.NonNull('Type')
    default_value = dauphin.String()
    is_optional = dauphin.NonNull(dauphin.Boolean)

    def __init__(self, name, field):
        super(DauphinTypeField, self).__init__(
            name=name,
            description=field.description,
            default_value=field.default_value_as_str if field.default_provided else None,
            is_optional=field.is_optional,
        )
        self._field = field

    def resolve_type(self, info):
        return info.schema.type_named('Type').to_dauphin_type(info, self._field.config_type)
