from collections.abc import Sequence

import graphene
from dagster._core.remote_representation.external_data import EnvVarConsumer

from dagster_graphql.schema.errors import GraphenePythonError
from dagster_graphql.schema.util import non_null_list


class GrapheneEnvVarConsumerType(graphene.Enum):
    RESOURCE = "RESOURCE"

    class Meta:
        name = "EnvVarConsumerType"


class GrapheneEnvVarConsumer(graphene.ObjectType):
    type = graphene.NonNull(GrapheneEnvVarConsumerType)
    name = graphene.NonNull(graphene.String)

    class Meta:
        name = "EnvVarConsumer"

    def __init__(self, env_var_consumer: EnvVarConsumer):
        super().__init__()

        self.type = GrapheneEnvVarConsumerType.RESOURCE
        self.name = env_var_consumer.name


class GrapheneEnvVarWithConsumers(graphene.ObjectType):
    envVarName = graphene.NonNull(graphene.String)
    envVarConsumers = graphene.Field(
        non_null_list(GrapheneEnvVarConsumer),
    )

    class Meta:
        name = "EnvVarWithConsumers"

    def __init__(self, name: str, consumers: Sequence[EnvVarConsumer]):
        super().__init__()

        self.envVarName = name
        self.consumers = consumers

    def resolve_envVarConsumers(self, _graphene_info) -> list[GrapheneEnvVarConsumer]:
        return [GrapheneEnvVarConsumer(consumer) for consumer in self.consumers]


class GrapheneEnvVarWithConsumersList(graphene.ObjectType):
    results = non_null_list(GrapheneEnvVarWithConsumers)

    class Meta:
        name = "EnvVarWithConsumersList"


class GrapheneEnvVarWithConsumersListOrError(graphene.Union):
    class Meta:
        types = (GrapheneEnvVarWithConsumersList, GraphenePythonError)
        name = "EnvVarWithConsumersOrError"
