from dagster.core.host_representation.grpc_server_registry import ProcessGrpcServerRegistry
from dagster.core.workspace.dynamic_workspace import DynamicWorkspace
from dagster.daemon import get_default_daemon_logger
from dagster.daemon.sensor import execute_sensor_iteration
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    infer_instigation_selector,
    infer_repository_selector,
)

from .graphql_context_test_suite import (  # get_dict_recon_repo,
    GraphQLContextVariant,
    make_graphql_context_test_suite,
)

INSTIGATION_QUERY = """
query JobQuery($instigationSelector: InstigationSelector!) {
  instigationStateOrError(instigationSelector: $instigationSelector) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on InstigationState {
        id
        nextTick {
            timestamp
        }
    }
  }
}
"""


def _create_sensor_tick(instance):
    with ProcessGrpcServerRegistry() as grpc_server_registry:
        with DynamicWorkspace(grpc_server_registry) as workspace:
            list(
                execute_sensor_iteration(
                    instance, get_default_daemon_logger("SensorDaemon"), workspace
                )
            )


class TestNextTickRepository(
    make_graphql_context_test_suite(
        context_variants=GraphQLContextVariant.all_non_launchable_variants(),
    )
):
    def test_schedule_next_tick(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        external_repository = graphql_context.get_repository_location(
            repository_selector["repositoryLocationName"]
        ).get_repository(repository_selector["repositoryName"])
        graphql_context.instance.reconcile_scheduler_state(external_repository)

        schedule_name = "no_config_pipeline_hourly_schedule"
        external_schedule = external_repository.get_external_schedule(schedule_name)
        selector = infer_instigation_selector(graphql_context, schedule_name)

        # need to be running in order to generate a future tick
        graphql_context.instance.start_schedule_and_update_storage_state(external_schedule)
        result = execute_dagster_graphql(
            graphql_context, INSTIGATION_QUERY, variables={"instigationSelector": selector}
        )

        assert result.data
        assert result.data["instigationStateOrError"]["__typename"] == "InstigationState"
        next_tick = result.data["instigationStateOrError"]["nextTick"]
        assert next_tick

    def test_sensor_next_tick(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        external_repository = graphql_context.get_repository_location(
            repository_selector["repositoryLocationName"]
        ).get_repository(repository_selector["repositoryName"])
        graphql_context.instance.reconcile_scheduler_state(external_repository)

        sensor_name = "always_no_config_sensor"
        external_sensor = external_repository.get_external_sensor(sensor_name)
        selector = infer_instigation_selector(graphql_context, sensor_name)

        # need to be running and create a sensor tick in the last 30 seconds in order to generate a
        # future tick
        graphql_context.instance.start_sensor(external_sensor)
        _create_sensor_tick(graphql_context.instance)

        result = execute_dagster_graphql(
            graphql_context, INSTIGATION_QUERY, variables={"instigationSelector": selector}
        )

        assert result.data
        assert result.data["instigationStateOrError"]["__typename"] == "InstigationState"
        next_tick = result.data["instigationStateOrError"]["nextTick"]
        assert next_tick
