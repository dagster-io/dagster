import time
import warnings
from abc import ABC
from collections.abc import Generator, Iterator, Sequence
from contextlib import contextmanager
from typing import Optional, Union, cast
from unittest import mock

from dagster import AssetCheckKey, AssetKey, BetaWarning
from dagster._core.definitions.assets.graph.remote_asset_graph import RemoteAssetNode
from dagster._core.definitions.assets.job.asset_job import IMPLICIT_ASSET_JOB_NAME
from dagster._core.definitions.selector import JobSelector, ScheduleSelector, SensorSelector
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.remote_representation.external import (
    CompoundID,
    RemoteJob,
    RemoteSchedule,
    RemoteSensor,
)
from dagster._core.utils import make_new_backfill_id
from dagster._core.workspace.context import RemoteDefinition, WorkspaceRequestContext
from dagster._core.workspace.permissions import Permissions
from dagster_graphql.client.query import (
    LAUNCH_PARTITION_BACKFILL_MUTATION,
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
    LAUNCH_PIPELINE_REEXECUTION_MUTATION,
)
from dagster_graphql.test.utils import (
    GqlAssetKey,
    execute_dagster_graphql,
    infer_job_selector,
    infer_schedule_selector,
    infer_sensor_selector,
)

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    GraphQLContextVariant,
    make_graphql_context_test_suite,
)
from dagster_graphql_tests.graphql.test_partition_backfill import CANCEL_BACKFILL_MUTATION
from dagster_graphql_tests.graphql.test_runs import DELETE_RUN_MUTATION
from dagster_graphql_tests.graphql.test_scheduler import START_SCHEDULES_QUERY, STOP_SCHEDULES_QUERY
from dagster_graphql_tests.graphql.test_sensors import START_SENSORS_QUERY

warnings.filterwarnings("ignore", category=BetaWarning, message=r"Parameter `owners` .*")

BaseTestSuite = make_graphql_context_test_suite(
    # no need to test all storages... just pick one that supports launching
    context_variants=[
        GraphQLContextVariant.sqlite_with_default_run_launcher_managed_grpc_env(
            None, "test_location"
        ),
    ]
)


class BaseDefinitionOwnerPermissionsTestSuite(ABC):
    def get_owned_definitions(self) -> set[Union[str, AssetKey]]:
        return set(
            [
                AssetKey(["owned_asset"]),
                AssetKey(["owned_partitioned_asset"]),
                "owned_job",
                "owned_partitioned_job",
                "owned_schedule",
                "owned_sensor",
            ]
        )

    def get_unowned_definitions(self) -> set[Union[str, AssetKey]]:
        return set(
            [
                AssetKey(["unowned_asset"]),
                AssetKey(["unowned_partitioned_asset"]),
                "unowned_job",
                "unowned_partitioned_job",
                "unowned_schedule",
                "unowned_sensor",
            ]
        )

    def _get_selector(
        self, context, def_type: type[RemoteDefinition], def_handle: Union[str, AssetKey]
    ) -> Union[AssetKey, JobSelector, ScheduleSelector, SensorSelector]:
        if isinstance(def_handle, AssetKey):
            return def_handle

        assert type(def_handle) is str
        if def_type is RemoteJob:
            return JobSelector.from_graphql_input(infer_job_selector(context, def_handle))
        if def_type is RemoteSensor:
            return SensorSelector.from_graphql_input(infer_sensor_selector(context, def_handle))
        if def_type is RemoteSchedule:
            return ScheduleSelector.from_graphql_input(infer_schedule_selector(context, def_handle))
        raise Exception(f"Unknown definition type {def_type}")

    def get_partition_set_by_job_name(self, context, job_name: str):
        job_selector = JobSelector.from_graphql_input(infer_job_selector(context, job_name))
        repository = context.get_code_location(job_selector.location_name).get_repository(
            job_selector.repository_name
        )
        return next(
            iter(ps for ps in repository.get_partition_sets() if ps.job_name == job_name), None
        )

    def graphql_launch_asset_backfill(self, context, asset_keys: list[AssetKey]):
        result = execute_dagster_graphql(
            context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "partitionNames": ["a", "b", "c"],
                    "assetSelection": [key.to_graphql_input() for key in asset_keys],
                }
            },
        )
        assert result.data
        typename = result.data["launchPartitionBackfill"]["__typename"]
        backfill_id = (
            result.data["launchPartitionBackfill"].get("backfillId")
            if typename == "LaunchBackfillSuccess"
            else None
        )
        return typename, backfill_id

    def graphql_launch_job_backfill(self, context, job_name: str):
        partition_set = self.get_partition_set_by_job_name(context, job_name)
        assert partition_set is not None

        result = execute_dagster_graphql(
            context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": {
                            "repositoryLocationName": partition_set.repository_handle.location_name,
                            "repositoryName": partition_set.repository_handle.repository_name,
                        },
                        "partitionSetName": partition_set.name,
                    },
                    "partitionNames": ["a", "b", "c"],
                }
            },
        )
        assert result.data
        typename = result.data["launchPartitionBackfill"]["__typename"]
        backfill_id = (
            result.data["launchPartitionBackfill"].get("backfillId")
            if typename == "LaunchBackfillSuccess"
            else None
        )
        return typename, backfill_id

    def graphql_cancel_backfill(self, context, backfill_id: str):
        result = execute_dagster_graphql(
            context,
            CANCEL_BACKFILL_MUTATION,
            variables={"backfillId": backfill_id},
        )
        assert result.data
        return result.data["cancelPartitionBackfill"]["__typename"]

    def graphql_launch_asset_run(self, context, asset_selection: list[AssetKey]):
        gql_asset_selection = (
            cast("Sequence[GqlAssetKey]", [key.to_graphql_input() for key in asset_selection])
            if asset_selection
            else None
        )
        selector = infer_job_selector(
            context,
            IMPLICIT_ASSET_JOB_NAME,
            asset_selection=gql_asset_selection,
        )
        result = execute_dagster_graphql(
            context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                }
            },
        )
        assert result.data
        return result.data["launchPipelineExecution"]["__typename"]

    def graphql_launch_job_run(self, context, job_name: str):
        selector = infer_job_selector(context, job_name)

        result = execute_dagster_graphql(
            context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                }
            },
        )
        assert result.data
        typename = result.data["launchPipelineExecution"]["__typename"]
        run_id = (
            result.data["launchPipelineExecution"]["run"]["runId"]
            if typename == "LaunchRunSuccess"
            else None
        )
        return typename, run_id

    def graphql_launch_asset_job(
        self, context, asset_selection: list[AssetKey], asset_check_selection: list[AssetCheckKey]
    ):
        selector = infer_job_selector(
            context,
            IMPLICIT_ASSET_JOB_NAME,
            asset_selection=[{"path": asset_key.path} for asset_key in asset_selection],
            asset_check_selection=[
                {"assetKey": {"path": check_key.asset_key.path}, "name": check_key.name}
                for check_key in asset_check_selection
            ],
        )
        result = execute_dagster_graphql(
            context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
        )
        assert result.data
        return result.data["launchPipelineExecution"]["__typename"]

    def graphql_launch_job_reexecution(
        self,
        context,
        job_name: str,
        run_id: str,
        asset_selection: Optional[list[AssetKey]] = None,
        asset_check_selection: Optional[list[AssetCheckKey]] = None,
    ):
        selector = infer_job_selector(
            context,
            job_name,
            asset_selection=[{"path": key.path} for key in asset_selection]
            if asset_selection
            else None,
            asset_check_selection=[
                {"assetKey": {"path": check_key.asset_key.path}, "name": check_key.name}
                for check_key in asset_check_selection
            ]
            if asset_check_selection
            else None,
        )

        result = execute_dagster_graphql(
            context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "executionMetadata": {
                        "rootRunId": run_id,
                        "parentRunId": run_id,
                    },
                    "mode": "default",
                }
            },
        )
        assert result.data
        return result.data["launchPipelineReexecution"]["__typename"]

    def graphql_start_schedule(self, context, schedule_name: str):
        selector = infer_schedule_selector(context, schedule_name)

        result = execute_dagster_graphql(
            context,
            START_SCHEDULES_QUERY,
            variables={
                "scheduleSelector": selector,
            },
        )
        assert result.data
        typename = result.data["startSchedule"]["__typename"]
        schedule_id = (
            result.data["startSchedule"]["scheduleState"]["id"]
            if typename == "ScheduleStateResult"
            else None
        )
        return typename, schedule_id

    def graphql_stop_schedule(self, context, schedule_id: str):
        result = execute_dagster_graphql(
            context,
            STOP_SCHEDULES_QUERY,
            variables={"id": schedule_id},
        )
        assert result.data
        return result.data["stopRunningSchedule"]["__typename"]

    def _create_started_schedule_state(self, context, schedule_name: str):
        selector = infer_schedule_selector(context, schedule_name)
        schedule = context.get_schedule(ScheduleSelector.from_graphql_input(selector))
        stored_state = context.instance.start_schedule(schedule)
        return CompoundID(
            remote_origin_id=stored_state.instigator_origin_id,
            selector_id=stored_state.selector_id,
        ).to_string()

    def graphql_start_sensor(self, context, sensor_name: str):
        selector = infer_sensor_selector(context, sensor_name)
        result = execute_dagster_graphql(
            context,
            START_SENSORS_QUERY,
            variables={
                "sensorSelector": selector,
            },
        )
        assert result.data
        return result.data["startSensor"]["__typename"]

    def graphql_update_sensor_cursor(self, context, sensor_name: str):
        selector = infer_sensor_selector(context, sensor_name)
        result = execute_dagster_graphql(
            context,
            """
            mutation SetSensorCursorMutation($sensorSelector: SensorSelector!, $cursor: String) {
                setSensorCursor(sensorSelector: $sensorSelector, cursor: $cursor) {
                    __typename
                    ... on Sensor {
                        name
                    }
                    ... on UnauthorizedError {
                        message
                    }
                }
            }
            """,
            variables={
                "sensorSelector": selector,
                "cursor": "new_cursor_value",
            },
        )
        assert result.data
        return result.data["setSensorCursor"]["__typename"]

    def graphql_delete_run(self, context, run_id: str):
        result = execute_dagster_graphql(context, DELETE_RUN_MUTATION, variables={"runId": run_id})
        assert result.data
        return result.data["deletePipelineRun"]["__typename"]

    def _create_run(self, context, job_name):
        remote_job = context.get_full_job(
            JobSelector.from_graphql_input(infer_job_selector(context, job_name))
        )
        repository = context.get_code_location(
            remote_job.repository_handle.location_name
        ).get_repository(remote_job.repository_handle.repository_name)
        return context.instance.create_run(
            job_name=job_name,
            run_id=None,
            run_config=None,
            status=None,
            tags=None,
            root_run_id=None,
            parent_run_id=None,
            step_keys_to_execute=None,
            execution_plan_snapshot=None,
            job_snapshot=None,
            parent_job_snapshot=None,
            asset_selection=None,
            asset_check_selection=None,
            resolved_op_selection=None,
            op_selection=None,
            job_code_origin=None,
            remote_job_origin=remote_job.get_remote_origin(),
            asset_graph=repository.asset_graph,
        )

    def _create_job_backfill(self, context: WorkspaceRequestContext, job_name: str):
        partition_set = self.get_partition_set_by_job_name(context, job_name)
        assert partition_set is not None
        backfill_id = make_new_backfill_id()
        partition_names = ["a", "b", "c"]
        backfill = PartitionBackfill(
            backfill_id=backfill_id,
            partition_set_origin=partition_set.get_remote_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=partition_names,
            from_failure=False,
            reexecution_steps=None,
            tags={},
            backfill_timestamp=time.time(),
            asset_selection=None,
            title=None,
            description=None,
            run_config=None,
        )
        context.instance.add_backfill(backfill)
        return backfill_id

    def _create_asset_backfill(self, context: WorkspaceRequestContext, asset_keys: list[AssetKey]):
        backfill_id = make_new_backfill_id()
        backfill = PartitionBackfill.from_asset_partitions(
            backfill_id=backfill_id,
            asset_graph=context.asset_graph,
            backfill_timestamp=time.time(),
            tags={},
            asset_selection=asset_keys,
            partition_names=None,
            dynamic_partitions_store=context.instance,
            all_partitions=True,
            title=None,
            description=None,
            run_config=None,
        )
        context.instance.add_backfill(backfill)
        return backfill_id

    def _get_type_for_handle(self, def_handle: Union[str, AssetKey]) -> type[RemoteDefinition]:
        if isinstance(def_handle, AssetKey):
            return RemoteAssetNode
        if def_handle.endswith("_job"):
            return RemoteJob
        elif def_handle.endswith("_schedule"):
            return RemoteSchedule
        elif def_handle.endswith("_sensor"):
            return RemoteSensor

        raise Exception(f"Unknown definition handle {def_handle}")

    def _create_run_with_asset_check_selection(
        self, context, asset_selection: list[AssetKey], asset_check_selection: list[AssetCheckKey]
    ):
        return context.instance.create_run(
            job_name=IMPLICIT_ASSET_JOB_NAME,
            run_id=None,
            run_config=None,
            status=None,
            tags=None,
            root_run_id=None,
            parent_run_id=None,
            step_keys_to_execute=None,
            execution_plan_snapshot=None,
            job_snapshot=None,
            parent_job_snapshot=None,
            asset_selection=set(asset_selection),
            asset_check_selection=set(asset_check_selection),
            resolved_op_selection=None,
            op_selection=None,
            job_code_origin=None,
            remote_job_origin=None,
            asset_graph=None,
        )

    def test_definitions_are_owned(self, graphql_context: WorkspaceRequestContext):
        for def_handle in self.get_owned_definitions():
            def_type = self._get_type_for_handle(def_handle)
            selector = self._get_selector(graphql_context, def_type, def_handle)
            assert graphql_context.has_permission_for_selector(
                Permissions.LAUNCH_PIPELINE_EXECUTION, selector
            )
        for def_handle in self.get_unowned_definitions():
            def_type = self._get_type_for_handle(def_handle)
            selector = self._get_selector(graphql_context, def_type, def_handle)
            assert not graphql_context.has_permission_for_selector(
                Permissions.LAUNCH_PIPELINE_EXECUTION, selector
            )

    def test_asset_backfill_launch_permissions(self, graphql_context: WorkspaceRequestContext):
        typename, _ = self.graphql_launch_asset_backfill(
            graphql_context, [AssetKey(["owned_partitioned_asset"])]
        )
        assert typename == "LaunchBackfillSuccess"

        typename, _ = self.graphql_launch_asset_backfill(
            graphql_context, [AssetKey(["unowned_partitioned_asset"])]
        )
        assert typename == "UnauthorizedError"

        typename, _ = self.graphql_launch_asset_backfill(
            graphql_context,
            [AssetKey(["owned_partitioned_asset"]), AssetKey(["unowned_partitioned_asset"])],
        )
        assert typename == "UnauthorizedError"

    def test_asset_backfill_cancel_permissions(self, graphql_context: WorkspaceRequestContext):
        backfill_id_a = self._create_asset_backfill(
            graphql_context, [AssetKey(["owned_partitioned_asset"])]
        )
        backfill_id_b = self._create_asset_backfill(
            graphql_context, [AssetKey(["unowned_partitioned_asset"])]
        )
        assert backfill_id_a
        assert backfill_id_b

        assert (
            self.graphql_cancel_backfill(graphql_context, backfill_id_a) == "CancelBackfillSuccess"
        )
        assert self.graphql_cancel_backfill(graphql_context, backfill_id_b) == "UnauthorizedError"

    def test_asset_run_launch_permissions(self, graphql_context: WorkspaceRequestContext):
        assert (
            self.graphql_launch_asset_run(graphql_context, [AssetKey(["owned_asset"])])
            == "LaunchRunSuccess"
        )
        assert (
            self.graphql_launch_asset_run(graphql_context, [AssetKey(["unowned_asset"])])
            == "UnauthorizedError"
        )
        assert (
            self.graphql_launch_asset_run(
                graphql_context, [AssetKey(["owned_asset"]), AssetKey(["unowned_asset"])]
            )
            == "UnauthorizedError"
        )

    def test_job_run_launch_permissions(self, graphql_context: WorkspaceRequestContext):
        typename, _ = self.graphql_launch_job_run(graphql_context, "owned_job")
        assert typename == "LaunchRunSuccess"

        typename, _ = self.graphql_launch_job_run(graphql_context, "unowned_job")
        assert typename == "UnauthorizedError"

    def test_job_reexecution_permissions(self, graphql_context: WorkspaceRequestContext):
        run_a = self._create_run(graphql_context, "owned_job")
        run_b = self._create_run(graphql_context, "unowned_job")
        assert (
            self.graphql_launch_job_reexecution(graphql_context, "owned_job", run_a.run_id)
            == "LaunchRunSuccess"
        )
        assert (
            self.graphql_launch_job_reexecution(graphql_context, "unowned_job", run_b.run_id)
            == "UnauthorizedError"
        )

    def test_start_schedule_permissions(self, graphql_context: WorkspaceRequestContext):
        typename, _ = self.graphql_start_schedule(graphql_context, "owned_schedule")
        assert typename == "ScheduleStateResult"

        typename, _ = self.graphql_start_schedule(graphql_context, "unowned_schedule")
        assert typename == "UnauthorizedError"

    def test_stop_schedule_permissions(self, graphql_context: WorkspaceRequestContext):
        schedule_a_id = self._create_started_schedule_state(graphql_context, "owned_schedule")
        schedule_b_id = self._create_started_schedule_state(graphql_context, "unowned_schedule")
        assert self.graphql_stop_schedule(graphql_context, schedule_a_id) == "ScheduleStateResult"
        assert self.graphql_stop_schedule(graphql_context, schedule_b_id) == "UnauthorizedError"

    def test_sensor_permissions(self, graphql_context: WorkspaceRequestContext):
        assert self.graphql_start_sensor(graphql_context, "owned_sensor") == "Sensor"
        assert self.graphql_start_sensor(graphql_context, "unowned_sensor") == "UnauthorizedError"
        assert self.graphql_update_sensor_cursor(graphql_context, "owned_sensor") == "Sensor"
        assert (
            self.graphql_update_sensor_cursor(graphql_context, "unowned_sensor")
            == "UnauthorizedError"
        )

    def test_run_deletion_permissions(self, graphql_context: WorkspaceRequestContext):
        run_a = self._create_run(graphql_context, "owned_job")
        run_b = self._create_run(graphql_context, "unowned_job")
        assert self.graphql_delete_run(graphql_context, run_a.run_id) == "DeletePipelineRunSuccess"
        assert self.graphql_delete_run(graphql_context, run_b.run_id) == "UnauthorizedError"

    def test_job_backfill_launch_permissions(self, graphql_context: WorkspaceRequestContext):
        typename, _ = self.graphql_launch_job_backfill(graphql_context, "owned_partitioned_job")
        assert typename == "LaunchBackfillSuccess"

        typename, _ = self.graphql_launch_job_backfill(graphql_context, "unowned_partitioned_job")
        assert typename == "UnauthorizedError"

    def test_job_backfill_cancel_permissions(self, graphql_context: WorkspaceRequestContext):
        backfill_id_a = self._create_job_backfill(graphql_context, "owned_partitioned_job")
        backfill_id_b = self._create_job_backfill(graphql_context, "unowned_partitioned_job")
        assert (
            self.graphql_cancel_backfill(graphql_context, backfill_id_a) == "CancelBackfillSuccess"
        )
        assert self.graphql_cancel_backfill(graphql_context, backfill_id_b) == "UnauthorizedError"

    def test_asset_check_run_launch_permissions(self, graphql_context: WorkspaceRequestContext):
        assert (
            self.graphql_launch_asset_job(
                graphql_context, [], [AssetCheckKey(AssetKey(["owned_asset"]), "owned_asset_check")]
            )
            == "LaunchRunSuccess"
        )
        assert (
            self.graphql_launch_asset_job(
                graphql_context,
                [],
                [AssetCheckKey(AssetKey(["unowned_asset"]), "unowned_asset_check")],
            )
            == "UnauthorizedError"
        )

    def test_mixed_asset_and_check_run_launch_permissions(
        self, graphql_context: WorkspaceRequestContext
    ):
        assert (
            self.graphql_launch_asset_job(
                graphql_context,
                [AssetKey(["owned_asset"])],
                [AssetCheckKey(AssetKey(["owned_asset"]), "owned_asset_check")],
            )
            == "LaunchRunSuccess"
        )
        assert (
            self.graphql_launch_asset_job(
                graphql_context,
                [AssetKey(["unowned_asset"])],
                [AssetCheckKey(AssetKey(["unowned_asset"]), "unowned_asset_check")],
            )
            == "UnauthorizedError"
        )
        assert (
            self.graphql_launch_asset_job(
                graphql_context,
                [AssetKey(["owned_asset"])],
                [AssetCheckKey(AssetKey(["unowned_asset"]), "unowned_asset_check")],
            )
            == "UnauthorizedError"
        )
        assert (
            self.graphql_launch_asset_job(
                graphql_context,
                [AssetKey(["unowned_asset"])],
                [AssetCheckKey(AssetKey(["owned_asset"]), "owned_asset_check")],
            )
            == "UnauthorizedError"
        )

    def test_asset_check_reexecution_permissions(self, graphql_context: WorkspaceRequestContext):
        run_with_owned = self._create_run_with_asset_check_selection(
            graphql_context,
            asset_selection=[AssetKey(["owned_asset"])],
            asset_check_selection=[AssetCheckKey(AssetKey(["owned_asset"]), "owned_asset_check")],
        )

        run_with_unowned = self._create_run_with_asset_check_selection(
            graphql_context,
            asset_selection=[AssetKey(["unowned_asset"])],
            asset_check_selection=[
                AssetCheckKey(AssetKey(["unowned_asset"]), "unowned_asset_check")
            ],
        )
        assert (
            self.graphql_launch_job_reexecution(
                graphql_context,
                IMPLICIT_ASSET_JOB_NAME,
                run_with_owned.run_id,
                asset_selection=[AssetKey(["owned_asset"])],
                asset_check_selection=[
                    AssetCheckKey(AssetKey(["owned_asset"]), "owned_asset_check")
                ],
            )
            == "LaunchRunSuccess"
        )
        assert (
            self.graphql_launch_job_reexecution(
                graphql_context,
                IMPLICIT_ASSET_JOB_NAME,
                run_with_unowned.run_id,
                asset_selection=[AssetKey(["unowned_asset"])],
                asset_check_selection=[
                    AssetCheckKey(AssetKey(["unowned_asset"]), "unowned_asset_check")
                ],
            )
            == "UnauthorizedError"
        )


class TestDefinitionOwnerPermissions(
    BaseDefinitionOwnerPermissionsTestSuite,
    BaseTestSuite,
):
    @contextmanager
    def yield_graphql_context(
        self, class_scoped_context
    ) -> Generator[WorkspaceRequestContext, None, None]:
        with super().yield_graphql_context(class_scoped_context) as context:
            with self.setup_permissions(context):
                yield context

    @contextmanager
    def setup_permissions(self, context: WorkspaceRequestContext) -> Iterator[None]:
        _did_check = {}

        def _mock_unpermitted(permission: str, *args) -> bool:
            _did_check[permission] = True
            return False

        def _mock_selector_ownership(
            permission: str,
            selector: Union[JobSelector, ScheduleSelector, SensorSelector, AssetKey, AssetCheckKey],
        ) -> bool:
            owned_defs = self.get_owned_definitions()
            _did_check[permission] = True
            if isinstance(selector, AssetKey):
                return selector in owned_defs
            elif isinstance(selector, AssetCheckKey):
                # Asset checks inherit permissions from their underlying asset
                return selector.asset_key in owned_defs
            elif isinstance(selector, JobSelector):
                return selector.job_name in owned_defs
            elif isinstance(selector, ScheduleSelector):
                return selector.schedule_name in owned_defs
            elif isinstance(selector, SensorSelector):
                return selector.sensor_name in owned_defs
            return False

        def _mock_permission_check(permission):
            return _did_check.get(permission) or False

        with (
            mock.patch.object(
                context,
                "has_permission",
                side_effect=_mock_unpermitted,
            ),
            mock.patch.object(
                context,
                "has_permission_for_location",
                side_effect=_mock_unpermitted,
            ),
            mock.patch.object(
                context,
                "viewer_has_any_owner_definition_permissions",
                side_effect=lambda: True,
            ),
            mock.patch.object(
                context, "has_permission_for_selector", side_effect=_mock_selector_ownership
            ),
            mock.patch.object(
                context, "was_permission_checked", side_effect=_mock_permission_check
            ),
        ):
            yield
