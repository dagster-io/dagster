import pytest
from dagster.core.test_utils import create_test_daemon_workspace
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
        status
        canChangeStatus
    }
  }
}
"""


def _create_sensor_tick(graphql_context):
    with create_test_daemon_workspace(
        graphql_context.process_context.workspace_load_target
    ) as workspace:
        list(
            execute_sensor_iteration(
                graphql_context.instance, get_default_daemon_logger("SensorDaemon"), workspace
            )
        )


class TestInstigation(
    make_graphql_context_test_suite(
        context_variants=GraphQLContextVariant.all_non_launchable_variants(),
    )
):
    def test_schedule_instigation(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        external_repository = graphql_context.get_repository_location(
            repository_selector["repositoryLocationName"]
        ).get_repository(repository_selector["repositoryName"])

        schedule_name = "no_config_pipeline_hourly_schedule"
        external_schedule = external_repository.get_external_schedule(schedule_name)
        selector = infer_instigation_selector(graphql_context, schedule_name)

        result = execute_dagster_graphql(
            graphql_context, INSTIGATION_QUERY, variables={"instigationSelector": selector}
        )

        assert result.data
        instigation_state = result.data["instigationStateOrError"]
        assert instigation_state["__typename"] == "InstigationState"
        assert not instigation_state["nextTick"]
        assert instigation_state["status"] == "STOPPED"
        assert instigation_state["canChangeStatus"] == True

        # need to be running in order to generate a future tick
        graphql_context.instance.start_schedule_and_update_storage_state(external_schedule)
        result = execute_dagster_graphql(
            graphql_context, INSTIGATION_QUERY, variables={"instigationSelector": selector}
        )

        assert result.data
        instigation_state = result.data["instigationStateOrError"]
        assert instigation_state["__typename"] == "InstigationState"
        assert instigation_state["nextTick"]
        assert instigation_state["status"] == "RUNNING"
        assert instigation_state["canChangeStatus"] == True

    def test_schedule_instigation_running_in_code(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        external_repository = graphql_context.get_repository_location(
            repository_selector["repositoryLocationName"]
        ).get_repository(repository_selector["repositoryName"])

        schedule_name = "no_config_pipeline_hourly_schedule_running_in_code"
        external_schedule = external_repository.get_external_schedule(schedule_name)
        selector = infer_instigation_selector(graphql_context, schedule_name)
        result = execute_dagster_graphql(
            graphql_context, INSTIGATION_QUERY, variables={"instigationSelector": selector}
        )

        assert result.data
        instigation_state = result.data["instigationStateOrError"]
        assert instigation_state["__typename"] == "InstigationState"
        assert instigation_state["nextTick"]
        assert instigation_state["status"] == "RUNNING"
        assert instigation_state["canChangeStatus"] == False

        with pytest.raises(
            Exception,
            match="Can only manually start a schedule that does not have its status set in code",
        ):
            graphql_context.instance.start_schedule_and_update_storage_state(external_schedule)

    def test_schedule_instigation_stopped_in_code(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        external_repository = graphql_context.get_repository_location(
            repository_selector["repositoryLocationName"]
        ).get_repository(repository_selector["repositoryName"])

        schedule_name = "no_config_pipeline_hourly_schedule_stopped_in_code"
        external_schedule = external_repository.get_external_schedule(schedule_name)
        selector = infer_instigation_selector(graphql_context, schedule_name)
        result = execute_dagster_graphql(
            graphql_context, INSTIGATION_QUERY, variables={"instigationSelector": selector}
        )

        assert result.data
        instigation_state = result.data["instigationStateOrError"]
        assert instigation_state["__typename"] == "InstigationState"
        assert not instigation_state["nextTick"]
        assert instigation_state["status"] == "STOPPED"
        assert instigation_state["canChangeStatus"] == False

        with pytest.raises(
            Exception,
            match="Can only manually start a schedule that does not have its status set in code",
        ):
            graphql_context.instance.start_schedule_and_update_storage_state(external_schedule)

    def test_sensor_instigation(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        external_repository = graphql_context.get_repository_location(
            repository_selector["repositoryLocationName"]
        ).get_repository(repository_selector["repositoryName"])

        sensor_name = "always_no_config_sensor"
        external_sensor = external_repository.get_external_sensor(sensor_name)
        selector = infer_instigation_selector(graphql_context, sensor_name)

        result = execute_dagster_graphql(
            graphql_context, INSTIGATION_QUERY, variables={"instigationSelector": selector}
        )

        assert result.data
        instigation_state = result.data["instigationStateOrError"]
        assert instigation_state["__typename"] == "InstigationState"
        assert not instigation_state["nextTick"]
        assert instigation_state["status"] == "STOPPED"
        assert instigation_state["canChangeStatus"] == True

        # need to be running and create a sensor tick in the last 30 seconds in order to generate a
        # future tick
        graphql_context.instance.start_sensor(external_sensor)
        _create_sensor_tick(graphql_context)

        result = execute_dagster_graphql(
            graphql_context, INSTIGATION_QUERY, variables={"instigationSelector": selector}
        )

        assert result.data
        instigation_state = result.data["instigationStateOrError"]
        assert instigation_state["__typename"] == "InstigationState"
        assert instigation_state["nextTick"]
        assert instigation_state["status"] == "RUNNING"
        assert instigation_state["canChangeStatus"] == True

    def test_sensor_instigation_running_in_code(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        external_repository = graphql_context.get_repository_location(
            repository_selector["repositoryLocationName"]
        ).get_repository(repository_selector["repositoryName"])

        sensor_name = "always_no_config_sensor_running_in_code"
        external_sensor = external_repository.get_external_sensor(sensor_name)
        selector = infer_instigation_selector(graphql_context, sensor_name)

        result = execute_dagster_graphql(
            graphql_context, INSTIGATION_QUERY, variables={"instigationSelector": selector}
        )

        assert result.data
        instigation_state = result.data["instigationStateOrError"]
        assert instigation_state["__typename"] == "InstigationState"
        assert not instigation_state["nextTick"]
        assert instigation_state["status"] == "RUNNING"
        assert instigation_state["canChangeStatus"] == False

        _create_sensor_tick(graphql_context)

        result = execute_dagster_graphql(
            graphql_context, INSTIGATION_QUERY, variables={"instigationSelector": selector}
        )

        assert result.data
        instigation_state = result.data["instigationStateOrError"]
        assert instigation_state["__typename"] == "InstigationState"
        assert instigation_state["nextTick"]
        assert instigation_state["status"] == "RUNNING"
        assert instigation_state["canChangeStatus"] == False

        with pytest.raises(
            Exception,
            match="Can only manually start a sensor that does not have its status set in code",
        ):
            graphql_context.instance.start_sensor(external_sensor)

    def test_sensor_instigation_stopped_in_code(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        external_repository = graphql_context.get_repository_location(
            repository_selector["repositoryLocationName"]
        ).get_repository(repository_selector["repositoryName"])

        sensor_name = "always_no_config_sensor_stopped_in_code"
        external_sensor = external_repository.get_external_sensor(sensor_name)
        selector = infer_instigation_selector(graphql_context, sensor_name)

        result = execute_dagster_graphql(
            graphql_context, INSTIGATION_QUERY, variables={"instigationSelector": selector}
        )

        assert result.data
        instigation_state = result.data["instigationStateOrError"]
        assert instigation_state["__typename"] == "InstigationState"
        assert not instigation_state["nextTick"]
        assert instigation_state["status"] == "STOPPED"
        assert instigation_state["canChangeStatus"] == False

        with pytest.raises(
            Exception,
            match="Can only manually start a sensor that does not have its status set in code",
        ):
            graphql_context.instance.start_sensor(external_sensor)
