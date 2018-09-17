import graphene

from dagster import (
    ConfigDefinition,
    ExpectationDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    SolidDefinition,
    check,
)

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
        self._pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)

    def resolve_solids(self, _info):
        return [
            Solid(
                solid, self._pipeline.dependency_structure.deps_of_solid_with_input(solid.name),
                self._pipeline.dependency_structure.depended_by_of_solid(solid.name)
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
        self._context = check.inst_param(context, 'context', PipelineContextDefinition)

    def resolve_config(self, _info):
        return Config(self._context.config_def)


class Solid(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    inputs = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Input)))
    outputs = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Output)))
    config = graphene.NonNull(lambda: Config)

    def __init__(self, solid, depends_on=None, depended_by=None):
        super(Solid, self).__init__(name=solid.name, description=solid.description)

        self._solid = check.inst_param(solid, 'solid', SolidDefinition)

        if depends_on:
            self._depends_on = {
                input_handle.input_def.name: output_handle
                for input_handle, output_handle in depends_on.items()
            }
        else:
            self.depends_on = {}

        if depended_by:
            self._depended_by = {
                output_handle.output_def.name: input_handles
                for output_handle, input_handles in depended_by.items()
            }
        else:
            self._depended_by = {}

    def resolve_inputs(self, _info):
        return [
            Input(input_definition, self, self._depends_on.get(input_definition.name))
            for input_definition in self._solid.input_defs
        ]

    def resolve_outputs(self, _info):
        return [
            Output(output_definition, self, self._depended_by.get(output_definition.name, []))
            for output_definition in self._solid.output_defs
        ]

    def resolve_config(self, _info):
        return Config(self._solid.config_def)


class Input(graphene.ObjectType):
    solid = graphene.NonNull(lambda: Solid)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type = graphene.NonNull(lambda: Type)
    expectations = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Expectation)))
    depends_on = graphene.Field(lambda: Output)

    def __init__(self, input_definition, solid, depends_on):
        super(Input, self).__init__(
            name=input_definition.name,
            description=input_definition.description,
            solid=solid,
        )
        self._input_definition = check.inst_param(
            input_definition, 'input_definition', InputDefinition
        )
        self._depends_on = depends_on

    def resolve_type(self, _info):
        return Type.from_dagster_type(dagster_type=self._input_definition.dagster_type)

    def resolve_expectations(self, _info):
        if self._input_definition.expectations:
            return [Expectation(expectation for expectation in self._input_definition.expectations)]
        else:
            return []

    def resolve_depends_on(self, _info):
        return Output(
            self._depends_on.output_def,
            Solid(self._depends_on.solid),
            # XXX(freiksenet): This is not right
            []
        )


class Output(graphene.ObjectType):
    solid = graphene.NonNull(lambda: Solid)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type = graphene.NonNull(lambda: Type)
    expectations = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Expectation)))
    depended_by = graphene.List(lambda: graphene.NonNull(Input))

    def __init__(self, output_definition, solid, depended_by):
        check.inst_param(output_definition, 'output_definition', OutputDefinition)
        super(Output, self).__init__(
            name=output_definition.name,
            description=output_definition.description,
            solid=solid,
        )
        self._output_definition = output_definition
        self._depended_by = depended_by

    def resolve_type(self, _info):
        return Type.from_dagster_type(dagster_type=self._output_definition.dagster_type)

    def resolve_expectations(self, _info):
        if self._output_definition.expectations:
            return [
                Expectation(expectation) for expectation in self._output_definition.expectations
            ]
        else:
            return []

    def resolve_depends_on(self, _info):
        return [
            Input(
                depended_by.input_def,
                Solid(depended_by.solid),
                # XXX(freiksenet): This is not right
                None
            ) for depended_by in self._depended_by
        ]


class Expectation(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()

    def __init__(self, expectation):
        check.inst_param(expectation, 'expectation', ExpectationDefinition)
        super(Expectation, self).__init__(
            name=expectation.name, description=expectation.description
        )


class Config(graphene.ObjectType):
    type = graphene.NonNull(lambda: Type)

    def __init__(self, config_def):
        super(Config, self).__init__()
        self._config_def = check.inst_param(config_def, 'config_def', ConfigDefinition)

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
