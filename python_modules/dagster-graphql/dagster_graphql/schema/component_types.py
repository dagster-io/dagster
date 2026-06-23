import graphene
from graphene.types.generic import GenericScalar

from dagster_graphql.schema.errors import GraphenePythonError, GrapheneRepositoryLocationNotFound
from dagster_graphql.schema.util import non_null_list


class GrapheneJsonSchema(GenericScalar, graphene.Scalar):
    """A JSON Schema document, returned as a parsed JSON object."""

    class Meta:
        name = "JsonSchema"


class GrapheneComponentFormSchema(graphene.ObjectType):
    """A component's JSON Schema pre-split server-side for react-jsonschema-form.

    The raw ``schema`` carries Dagster-specific conventions (inline ``ui:*``
    hints, unset-default sentinels, Jinja string escape-hatch variants). Rather
    than have the frontend reverse-engineer those, the server splits the schema
    once via ``dagster.components.resolved.form_schema.split_form_schema`` and
    exposes the resulting RJSF-ready pair here.
    """

    dataSchema = graphene.NonNull(
        GrapheneJsonSchema,
        description="The cleaned JSON Schema RJSF validates and renders against.",
    )
    uiSchema = graphene.NonNull(
        GrapheneJsonSchema,
        description="The parallel RJSF uiSchema holding lifted ``ui:*`` hints.",
    )

    class Meta:
        name = "ComponentFormSchema"


class GrapheneComponentTypeInfo(graphene.ObjectType):
    """Metadata for a single Component class registered in a code location."""

    name = graphene.NonNull(graphene.String)
    namespace = graphene.NonNull(
        graphene.String,
        description="The plugin namespace this component belongs to (e.g. ``dagster_test``).",
    )
    example = graphene.NonNull(
        graphene.String,
        description=(
            "Sample YAML rendered server-side from the component's JSON Schema."
            " Used to seed the docs ``Example`` panel."
        ),
    )
    schema = graphene.Field(
        GrapheneJsonSchema,
        description=(
            "The JSON Schema describing the component's attributes model. May be"
            " null if the component does not declare a model."
        ),
    )
    formSchema = graphene.Field(
        GrapheneComponentFormSchema,
        description=(
            "The ``schema`` split server-side into the (dataSchema, uiSchema)"
            " pair react-jsonschema-form expects. Null when the component"
            " declares no model."
        ),
    )
    description = graphene.String()
    owners = graphene.List(graphene.NonNull(graphene.String))
    tags = graphene.List(graphene.NonNull(graphene.String))
    isAppManaged = graphene.NonNull(
        graphene.Boolean,
        description=(
            "Whether instances of this component class may be created and edited"
            " from the UI via the app-managed components workflow. Today every"
            " component class is editable; in the future this will be an opt-in"
            " hook on the Component class so library authors can mark their"
            " components app-managed explicitly."
        ),
    )

    class Meta:
        name = "ComponentTypeInfo"


class GrapheneComponentTypes(graphene.ObjectType):
    locationName = graphene.NonNull(graphene.String)
    componentTypes = non_null_list(GrapheneComponentTypeInfo)

    class Meta:
        name = "ComponentTypes"


class GrapheneComponentTypesOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneComponentTypes,
            GrapheneRepositoryLocationNotFound,
            GraphenePythonError,
        )
        name = "ComponentTypesOrError"


types = [
    GrapheneJsonSchema,
    GrapheneComponentFormSchema,
    GrapheneComponentTypeInfo,
    GrapheneComponentTypes,
    GrapheneComponentTypesOrError,
]
