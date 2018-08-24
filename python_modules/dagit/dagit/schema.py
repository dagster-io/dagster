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
        return [
            Solid(
                solid, self._pipeline.dependency_structure.deps_of_solid_with_input(solid.name),
                self._pipeline.dependency_structure.depended_by_of_solid(solid.name)
            ) for solid in self._pipeline.solids
        ]

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
    description = graphene.String()
    inputs = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Input)))
    outputs = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Output)))
    config = graphene.NonNull(graphene.List(lambda: graphene.NonNull(Argument)))

    def __init__(self, solid, depends_on=None, depended_by=None):
        super(Solid, self).__init__(name=solid.name, description=solid.description)
        self._solid = solid
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

    def resolve_inputs(self, info):
        return [
            Input(input_definition, self, self._depends_on.get(input_definition.name))
            for input_definition in self._solid.input_defs
        ]

    def resolve_outputs(self, info):
        return [
            Output(output_definition, self, self._depended_by.get(output_definition.name, []))
            for output_definition in self._solid.output_defs
        ]

    def resolve_config(self, info):
        return [
            Argument(name=name, argument=argument)
            for name, argument in self._solid.config_def.argument_def_dict.items()
        ]


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
        self._input_definition = input_definition
        self._depends_on = depends_on

    def resolve_type(self, info):
        return Type(dagster_type=self._input_definition.dagster_type)

    def resolve_expectations(self, info):
        if self._input_definition.expectations:
            return [Expectation(expectation for expectation in self._input_definition.expectations)]
        else:
            return []

    def resolve_depends_on(self, info):
        return Output(
            self._depends_on.output,
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
        super(Output, self).__init__(
            name=output_definition.name,
            description=output_definition.description,
            solid=solid,
        )
        self._output_definition = output_definition
        self._depended_by = depended_by

    def resolve_type(self, info):
        return Type(dagster_type=self._output_definition.dagster_type)

    def resolve_expectations(self, info):
        if self._output_definition.expectations:
            return [
                Expectation(expectation) for expectation in self._output_definition.expectations
            ]
        else:
            return []

    def resolve_depends_on(self, info):
        return [
            Input(
                depended_by.input_def,
                Solid(depended_by.solid),
                # XXX(freiksenet): This is not right
                None
            ) for depended_by in self._depended_by
        ]


class Argument(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    type = graphene.NonNull(lambda: Type)
    is_optional = graphene.NonNull(graphene.Boolean)

    def __init__(self, name, argument):
        super(Argument, self).__init__(
            name=name, description=argument.description, is_optional=argument.is_optional
        )
        self._argument = argument

    def resolve_type(self, info):
        return Type(dagster_type=self._argument.dagster_type)


class Expectation(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()

    def __init__(self, expectation):
        super(Expectation, self).__init__(
            name=expectation.name, description=expectation.description
        )


class Type(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()

    def __init__(self, dagster_type):
        super(Type, self).__init__(
            name=dagster_type.name,
            description=dagster_type.description,
        )


def create_schema():
    return graphene.Schema(query=Query)
