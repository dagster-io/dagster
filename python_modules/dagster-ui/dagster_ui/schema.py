import graphene


class Query(graphene.ObjectType):
    pipeline = graphene.Field(lambda: Pipeline, name=graphene.String())
    pipelines = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Pipeline)))

    def resolve_pipeline(self, info, name):
        config = info.context['pipeline_config']
        pipeline_config = config.get_pipeline(name)
        return Pipeline(pipeline_config.pipeline)

    def resolve_pipelines(self, info):
        config = info.context['pipeline_config']
        return [Pipeline(c.pipeline) for c in config.create_pipelines()]


# (XXX) Some stuff is named, other stuffed is keyed in dict.
# Either everything should be named or everything should be keyed


class Pipeline(graphene.ObjectType):
    # XXX(freiksenet): optional, but probably shouldn't be
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    solids = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Solid)))
    context = graphene.NonNull(graphene.List(lambda: graphene.NonNull(PipelineContext)))

    def __init__(self, pipeline):
        super(Pipeline, self).__init__(name=pipeline.name, description=pipeline.description)
        self._pipeline = pipeline

    def resolve_solids(self, info):
        return [Solid(solid) for solid in self._pipeline.solids]

    def resolve_context(self, info):
        return [
            PipelineContext(name=name, context=context)
            for name, context in self._pipeline.context_definitions.items()
        ]


class PipelineContext(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    arguments = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Argument)))

    def __init__(self, name, context):
        super(PipelineContext, self).__init__(name=name, description=context.description)
        self._context = context

    def resolve_arguments(self, info):
        return [
            Argument(name=name, argument=argument)
            for name, argument in self._context.argument_def_dict.items()
        ]


class Solid(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    # XXX(freiksenet): missing
    description = graphene.String()
    inputs = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Input)))
    output = graphene.Field(lambda: graphene.NonNull(Output))

    def __init__(self, solid):
        super(Solid, self).__init__(
            name=solid.name,
            # XXX(freiksenet): missing
            # description=context.description
        )
        self._solid = solid

    def resolve_inputs(self, info):
        return [Input(input_definition) for input_definition in self._solid.inputs]

    def resolve_output(self, info):
        return Output(self._solid.output)


class Input(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    # XXX(freiksenet): missing
    description = graphene.String()
    sources = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Source)))
    depends_on = graphene.Field(lambda: Solid)
    expectations = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Expectation)))

    def __init__(self, input_definition):
        super(Input, self).__init__(
            name=input_definition.name,
            # XXX(freiksenet): missing
            # description=input_definition.description
        )
        self._input_definition = input_definition

    def resolve_sources(self, info):
        return [Source(source) for source in self._input_definition.sources]

    def resolve_depends_on(self, info):
        if self._input_definition.depends_on:
            return Solid(self._input_definition.depends_on)
        else:
            return None

    def resolve_expectations(self, info):
        if self._input_definition.expectations:
            return [Expectation(expectation for expectation in self._input_definition.expectations)]
        else:
            return []


class Output(graphene.ObjectType):
    # XXX(freiksenet): should we have it? Prolly solid desc is enough
    # description = graphene.String()
    materializations = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Materialization)))
    expectations = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Expectation)))

    def __init__(self, output_definition):
        super(Output, self).__init__()
        self._output_definition = output_definition

    def resolve_materializations(self, info):
        if self._output_definition.materializations:
            return [
                Materialization(materialization)
                for materialization in self._output_definition.materializations
            ]
        else:
            return []

    def resolve_expectations(self, info):
        if self._output_definition.expectations:
            return [
                Expectation(expectation for expectation in self._output_definition.expectations)
            ]
        else:
            return []


class Source(graphene.ObjectType):
    # XXX(freiksenet): maybe rename to name?
    source_type = graphene.NonNull(graphene.String)
    # XXX(freiksenet): missing
    description = graphene.String()
    arguments = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Argument)))

    def __init__(self, source):
        super(Source, self).__init__(
            source_type=source.source_type,
            # XXX(freiksenet): missing
            # description=source.description
        )
        self._source = source

    def resolve_arguments(self, info):
        return [
            Argument(name=name, argument=argument)
            for name, argument in self._source.argument_def_dict.items()
        ]


class Materialization(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    # XXX(freiksenet): missing
    description = graphene.String()
    arguments = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Argument)))

    def __init__(self, materialization):
        super(Materialization, self).__init__(
            name=materialization.name,
            # XXX(freiksenet): missing
            # description=materialization.description
        )
        self._materialization = materialization

    def resolve_arguments(self, info):
        return [
            Argument(name=name, argument=argument)
            for name, argument in self._materialization.argument_def_dict.items()
        ]


class Type(graphene.Enum):
    STRING = 'String'
    PATH = 'Path'
    INT = 'Int'
    BOOL = 'Bool'


class Argument(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type = graphene.NonNull(lambda: Type)
    is_optional = graphene.NonNull(graphene.Boolean)

    def __init__(self, name, argument):
        super(Argument, self).__init__(
            name=name,
            description=argument.description,
            type=argument.dagster_type.name,
            is_optional=argument.is_optional
        )


class Expectation(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    # XXX(freiksenet): missing
    description = graphene.String()

    def __init__(self, expectation):
        super(Expectation, self).__init__(
            name=expectation.name,
            # XXX(freiksenet): missing
            # description=expectation.description
        )


def create_schema():
    return graphene.Schema(query=Query)
