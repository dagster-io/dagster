import graphene

import dagster
import dagster.core.definitions

from dagster import check

from dagster.core.types import DagsterCompositeType


class Query(graphene.ObjectType):
    pipeline = graphene.Field(lambda: Pipeline, name=graphene.String())
    pipelines = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Pipeline)))

    def resolve_pipeline(self, info, name):
        check.str_param(name, 'name')
        repository = info.context['repository_container'].repository
        return Pipeline(repository.get_pipeline(name))

    def resolve_pipelines(self, info):
        repository = info.context['repository_container'].repository
        pipelines = []
        for pipeline_def in repository.get_all_pipelines():
            pipelines.append(Pipeline(pipeline_def))
        return pipelines


class Pipeline(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    solids = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Solid)))
    contexts = graphene.NonNull(graphene.List(lambda: graphene.NonNull(PipelineContext)))

    def __init__(self, pipeline):
        super(Pipeline, self).__init__(name=pipeline.name, description=pipeline.description)
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


class PipelineContext(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    config = graphene.NonNull(lambda: Config)

    def __init__(self, name, context):
        super(PipelineContext, self).__init__(name=name, description=context.description)
        self._context = check.inst_param(context, 'context', dagster.PipelineContextDefinition)

    def resolve_config(self, _info):
        return Config(self._context.config_def)


class Solid(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    definition = graphene.NonNull(lambda: SolidDefinition)
    inputs = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Input)))
    outputs = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Output)))

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


class SolidDefinition(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    input_definitions = graphene.NonNull(graphene.List(lambda: graphene.NonNull(InputDefinition)))
    output_definitions = graphene.NonNull(graphene.List(lambda: graphene.NonNull(OutputDefinition)))
    config_definition = graphene.NonNull(lambda: Config)

    # solids - ?

    def __init__(self, solid_def):
        super(SolidDefinition, self).__init__(
            name=solid_def.name, description=solid_def.description
        )

        self._solid_def = check.inst_param(solid_def, 'solid_def', dagster.SolidDefinition)

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
        return Config(self._solid_def.config_def)


class InputDefinition(graphene.ObjectType):
    solid_definition = graphene.NonNull(lambda: SolidDefinition)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type = graphene.NonNull(lambda: Type)
    expectations = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Expectation)))

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
        return Type.from_dagster_type(dagster_type=self._input_definition.dagster_type)

    def resolve_expectations(self, _info):
        if self._input_definition.expectations:
            return [Expectation(expectation for expectation in self._input_definition.expectations)]
        else:
            return []


class OutputDefinition(graphene.ObjectType):
    solid_definition = graphene.NonNull(lambda: SolidDefinition)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type = graphene.NonNull(lambda: Type)
    expectations = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Expectation)))

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
        return Type.from_dagster_type(dagster_type=self._output_definition.dagster_type)

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
    type = graphene.NonNull(lambda: Type)

    def __init__(self, config_def):
        super(Config, self).__init__()
        self._config_def = check.inst_param(config_def, 'config_def', dagster.ConfigDefinition)

    def resolve_type(self, _info):
        return Type.from_dagster_type(dagster_type=self._config_def.config_type)


class Type(graphene.Interface):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()

    @classmethod
    def from_dagster_type(cls, dagster_type):
        if isinstance(dagster_type, DagsterCompositeType):
            return CompositeType(dagster_type)
        else:
            return RegularType(dagster_type)


class RegularType(graphene.ObjectType):
    class Meta:
        interfaces = [
            Type,
        ]

    def __init__(self, dagster_type):
        super(RegularType, self).__init__(
            name=dagster_type.name,
            description=dagster_type.description,
        )


class CompositeType(graphene.ObjectType):
    fields = graphene.NonNull(graphene.List(graphene.NonNull(lambda: TypeField)))

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

    def resolve_fields(self, _info):
        return [TypeField(name=k, field=v) for k, v in self._dagster_type.field_dict.items()]


class TypeField(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type = graphene.NonNull(lambda: Type)
    default_value = graphene.String()
    is_optional = graphene.NonNull(graphene.Boolean)

    def __init__(self, name, field):
        super(TypeField, self).__init__(
            name=name,
            description=field.description,
            default_value=str(field.default_value),
            is_optional=field.is_optional
        )
        self._field = field

    def resolve_type(self, _info):
        return Type.from_dagster_type(dagster_type=self._field.dagster_type)


def create_schema():
    return graphene.Schema(query=Query, types=[RegularType, CompositeType])
