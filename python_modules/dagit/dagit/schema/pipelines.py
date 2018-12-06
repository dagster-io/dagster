from __future__ import absolute_import
from functools import wraps
import graphene

import dagster
from dagster.core.types import DagsterCompositeType
from dagster import check

from .utils import non_null_list


def _pipeline_run():
    from dagit.schema import runs
    return runs.PipelineRun


class GraphenePipeline(graphene.ObjectType):
    class Meta:
        name = 'Pipeline'

    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    solids = non_null_list(lambda: Solid)
    contexts = non_null_list(lambda: PipelineContext)
    environment_type = graphene.NonNull(lambda: GrapheneDagsterType)
    types = graphene.NonNull(graphene.List(graphene.NonNull(lambda: GrapheneDagsterType)), )
    runs = non_null_list(_pipeline_run)

    def __init__(self, pipeline):
        super(GraphenePipeline, self).__init__(name=pipeline.name, description=pipeline.description)
        self._pipeline = check.inst_param(pipeline, 'pipeline', dagster.PipelineDefinition)

    def resolve_solids(self, _info):
        return [
            Solid(
                solid,
                self._pipeline.dependency_structure.deps_of_solid_with_input(solid.name),
                self._pipeline.dependency_structure.depended_by_of_solid(solid.name),
            ) for solid in self._pipeline.solids
        ]

    def resolve_contexts(self, _info):
        return [
            PipelineContext(name=name, context=context)
            for name, context in self._pipeline.context_definitions.items()
        ]

    def resolve_environment_type(self, _info):
        return GrapheneDagsterType.from_dagster_type(self._pipeline.environment_type)

    def resolve_types(self, _info):
        return sorted(
            [GrapheneDagsterType.from_dagster_type(type_) for type_ in self._pipeline.all_types()],
            key=lambda type_: type_.name
        )

    def resolve_runs(self, info):
        from dagit.schema import runs
        return [
            runs.PipelineRun(r)
            for r in info.context.pipeline_runs.all_runs_for_pipeline(self._pipeline.name)
        ]

    def get_dagster_pipeline(self):
        return self._pipeline

    def get_type(self, typeName):
        return GrapheneDagsterType.from_dagster_type(self._pipeline.type_named(typeName))


class PipelineConnection(graphene.ObjectType):
    nodes = non_null_list(lambda: GraphenePipeline)


class PipelineContext(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    config = graphene.Field(lambda: Config)

    def __init__(self, name, context):
        super(PipelineContext, self).__init__(name=name, description=context.description)
        self._context = check.inst_param(context, 'context', dagster.PipelineContextDefinition)

    def resolve_config(self, _info):
        return Config(self._context.config_field) if self._context.config_field else None


class Solid(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    definition = graphene.NonNull(lambda: SolidDefinition)
    inputs = non_null_list(lambda: Input)
    outputs = non_null_list(lambda: Output)

    def __init__(self, solid, depends_on=None, depended_by=None):
        super(Solid, self).__init__(name=solid.name)

        self._solid = check.inst_param(solid, 'solid', dagster.core.definitions.Solid)

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

    def resolve_definition(self, _info):
        return SolidDefinition(self._solid.definition)

    def resolve_inputs(self, _info):
        return [Input(input_handle, self) for input_handle in self._solid.input_handles()]

    def resolve_outputs(self, _info):
        return [Output(output_handle, self) for output_handle in self._solid.output_handles()]


class Input(graphene.ObjectType):
    solid = graphene.NonNull(lambda: Solid)
    definition = graphene.NonNull(lambda: InputDefinition)
    depends_on = graphene.Field(lambda: Output)

    def __init__(self, input_handle, solid):
        super(Input, self).__init__(solid=solid)
        self._solid = check.inst_param(solid, 'solid', Solid)
        self._input_handle = check.inst_param(
            input_handle, 'input_handle', dagster.core.definitions.SolidInputHandle
        )

    def resolve_definition(self, _info):
        return InputDefinition(self._input_handle.input_def, self._solid.resolve_definition({}))

    def resolve_depends_on(self, _info):
        if self._input_handle in self._solid.depends_on:
            return Output(
                self._solid.depends_on[self._input_handle],
                Solid(self._solid.depends_on[self._input_handle].solid),
            )
        else:
            return None


class Output(graphene.ObjectType):
    solid = graphene.NonNull(lambda: Solid)
    definition = graphene.NonNull(lambda: OutputDefinition)
    depended_by = graphene.List(lambda: graphene.NonNull(Input))

    def __init__(self, output_handle, solid):
        super(Output, self).__init__(solid=solid)
        self._solid = check.inst_param(solid, 'solid', Solid)
        self._output_handle = check.inst_param(
            output_handle, 'output_handle', dagster.core.definitions.SolidOutputHandle
        )

    def resolve_definition(self, _info):
        return OutputDefinition(self._output_handle.output_def, self._solid.resolve_definition({}))

    def resolve_depended_by(self, _info):
        return [
            Input(
                input_handle,
                Solid(input_handle.solid),
            ) for input_handle in self._solid.depended_by.get(self._output_handle, [])
        ]


class SolidMetadataItemDefinition(graphene.ObjectType):
    key = graphene.NonNull(graphene.String)
    value = graphene.NonNull(graphene.String)


class SolidDefinition(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    metadata = non_null_list(lambda: SolidMetadataItemDefinition)
    input_definitions = non_null_list(lambda: InputDefinition)
    output_definitions = non_null_list(lambda: OutputDefinition)
    config_definition = graphene.Field(lambda: Config)

    # solids - ?

    def __init__(self, solid_def):
        super(SolidDefinition, self).__init__(
            name=solid_def.name,
            description=solid_def.description,
        )

        self._solid_def = check.inst_param(solid_def, 'solid_def', dagster.SolidDefinition)

    def resolve_metadata(self, _info):
        return [
            SolidMetadataItemDefinition(key=item[0], value=item[1])
            for item in self._solid_def.metadata.items()
        ]

    def resolve_input_definitions(self, _info):
        return [
            InputDefinition(input_definition, self)
            for input_definition in self._solid_def.input_defs
        ]

    def resolve_output_definitions(self, _info):
        return [
            OutputDefinition(output_definition, self)
            for output_definition in self._solid_def.output_defs
        ]

    def resolve_config_definition(self, _info):
        return Config(self._solid_def.config_field) if self._solid_def.config_field else None


class InputDefinition(graphene.ObjectType):
    solid_definition = graphene.NonNull(lambda: SolidDefinition)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type = graphene.NonNull(lambda: GrapheneDagsterType)
    expectations = non_null_list(lambda: Expectation)

    # inputs - ?

    def __init__(self, input_definition, solid_def):
        super(InputDefinition, self).__init__(
            name=input_definition.name,
            description=input_definition.description,
            solid_definition=solid_def,
        )
        self._input_definition = check.inst_param(
            input_definition, 'input_definition', dagster.InputDefinition
        )

    def resolve_type(self, _info):
        return GrapheneDagsterType.from_dagster_type(
            dagster_type=self._input_definition.dagster_type
        )

    def resolve_expectations(self, _info):
        if self._input_definition.expectations:
            return [Expectation(expectation for expectation in self._input_definition.expectations)]
        else:
            return []


class OutputDefinition(graphene.ObjectType):
    solid_definition = graphene.NonNull(lambda: SolidDefinition)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type = graphene.NonNull(lambda: GrapheneDagsterType)
    expectations = non_null_list(lambda: Expectation)

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

    def resolve_type(self, _info):
        return GrapheneDagsterType.from_dagster_type(
            dagster_type=self._output_definition.dagster_type
        )

    def resolve_expectations(self, _info):
        if self._output_definition.expectations:
            return [
                Expectation(expectation) for expectation in self._output_definition.expectations
            ]
        else:
            return []


class Expectation(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()

    def __init__(self, expectation):
        check.inst_param(expectation, 'expectation', dagster.ExpectationDefinition)
        super(Expectation, self).__init__(
            name=expectation.name, description=expectation.description
        )


class Config(graphene.ObjectType):
    type = graphene.NonNull(lambda: GrapheneDagsterType)

    def __init__(self, config_field):
        super(Config, self).__init__()
        self._config_field = check.opt_inst_param(config_field, 'config_field', dagster.Field)

    def resolve_type(self, _info):
        return GrapheneDagsterType.from_dagster_type(dagster_type=self._config_field.dagster_type)


class TypeAttributes(graphene.ObjectType):
    is_builtin = graphene.NonNull(
        graphene.Boolean,
        description='''
True if the system defines it and it is the same type across pipelines.
Examples include "Int" and "String."''',
    )
    is_system_config = graphene.NonNull(
        graphene.Boolean,
        description='''
Dagster generates types for base elements of the config system (e.g. the solids and
context field of the base environment). These types are always present
and are typically not relevant to an end user. This flag allows tool authors to
filter out those types by default.
''',
    )


class GrapheneDagsterType(graphene.Interface):
    class Meta:
        name = 'Type'

    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type_attributes = graphene.NonNull(TypeAttributes)

    @classmethod
    def from_dagster_type(cls, dagster_type):
        if isinstance(dagster_type, DagsterCompositeType):
            return CompositeType(dagster_type)
        else:
            return RegularType(dagster_type)


class RegularType(graphene.ObjectType):
    class Meta:
        interfaces = [
            GrapheneDagsterType,
        ]

    def __init__(self, dagster_type):
        super(RegularType, self).__init__(
            name=dagster_type.name,
            description=dagster_type.description,
        )
        self._dagster_type = dagster_type

    def resolve_type_attributes(self, _info):
        return self._dagster_type.type_attributes


class CompositeType(graphene.ObjectType):
    fields = non_null_list(lambda: TypeField)

    class Meta:
        interfaces = [
            GrapheneDagsterType,
        ]

    def __init__(self, dagster_type):
        super(CompositeType, self).__init__(
            name=dagster_type.name,
            description=dagster_type.description,
        )
        self._dagster_type = dagster_type

    def resolve_type_attributes(self, _info):
        return self._dagster_type.type_attributes

    def resolve_fields(self, _info):
        return [TypeField(name=k, field=v) for k, v in self._dagster_type.field_dict.items()]


class TypeField(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type = graphene.NonNull(lambda: GrapheneDagsterType)
    default_value = graphene.String()
    is_optional = graphene.NonNull(graphene.Boolean)

    def __init__(self, name, field):
        super(TypeField, self).__init__(
            name=name,
            description=field.description,
            default_value=field.default_value_as_str if field.default_provided else None,
            is_optional=field.is_optional
        )
        self._field = field

    def resolve_type(self, _info):
        return GrapheneDagsterType.from_dagster_type(dagster_type=self._field.dagster_type)
