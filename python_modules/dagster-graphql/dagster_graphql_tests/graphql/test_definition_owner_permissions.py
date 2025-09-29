import time
from abc import ABC
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from typing import Union
from unittest import mock

from dagster import AssetKey
from dagster._core.definitions.assets.graph.remote_asset_graph import RemoteAssetNode
from dagster._core.definitions.selector import JobSelector, ScheduleSelector, SensorSelector
from dagster._core.execution.backfill import PartitionBackfill
from dagster._core.remote_representation.external import RemoteJob, RemoteSchedule, RemoteSensor
from dagster._core.utils import make_new_backfill_id
from dagster._core.workspace.context import RemoteDefinition, WorkspaceRequestContext
from dagster._core.workspace.permissions import Permissions
from dagster_graphql.client.query import LAUNCH_PARTITION_BACKFILL_MUTATION
from dagster_graphql.test.utils import (
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
            ]
        )

    def get_unowned_definitions(self) -> set[Union[str, AssetKey]]:
        return set(
            [
                AssetKey(["unowned_asset"]),
                AssetKey(["unowned_partitioned_asset"]),
            ]
        )

    def _get_remote_definition(
        self, context, def_type: type[RemoteDefinition], def_handle: Union[str, AssetKey]
    ) -> RemoteDefinition:
        if def_type is RemoteAssetNode:
            assert isinstance(def_handle, AssetKey)
            return context.asset_graph.get(def_handle)

        assert type(def_handle) is str
        if def_type is RemoteJob:
            job_selector = JobSelector.from_graphql_input(infer_job_selector(context, def_handle))
            return context.get_full_job(job_selector)
        if def_type is RemoteSensor:
            sensor_selector = SensorSelector.from_graphql_input(
                infer_sensor_selector(context, def_handle)
            )
            return context.get_sensor(sensor_selector)
        if def_type is RemoteSchedule:
            schedule_selector = ScheduleSelector.from_graphql_input(
                infer_schedule_selector(context, def_handle)
            )
            return context.get_schedule(schedule_selector)
        raise Exception(f"Unknown definition type {def_type}")

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

    def graphql_cancel_backfill(self, context, backfill_id: str):
        result = execute_dagster_graphql(
            context,
            CANCEL_BACKFILL_MUTATION,
            variables={"backfillId": backfill_id},
        )
        assert result.data
        return result.data["cancelPartitionBackfill"]["__typename"]

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

    def test_definitions_are_owned(self, graphql_context: WorkspaceRequestContext):
        for def_handle in self.get_owned_definitions():
            def_type = self._get_type_for_handle(def_handle)
            definition = self._get_remote_definition(graphql_context, def_type, def_handle)
            assert graphql_context.has_permission_for_definition(
                Permissions.LAUNCH_PIPELINE_EXECUTION, definition
            )
        for def_handle in self.get_unowned_definitions():
            def_type = self._get_type_for_handle(def_handle)
            definition = self._get_remote_definition(graphql_context, def_type, def_handle)
            assert not graphql_context.has_permission_for_definition(
                Permissions.LAUNCH_PIPELINE_EXECUTION, definition
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

        def _mock_definition_ownership(permission: str, definition: RemoteDefinition) -> bool:
            owned_defs = self.get_owned_definitions()
            _did_check[permission] = True
            if isinstance(definition, RemoteAssetNode):
                return definition.key in owned_defs
            elif isinstance(definition, (RemoteJob, RemoteSensor, RemoteSchedule)):
                return definition.name in owned_defs
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
                side_effect=lambda _: True,
            ),
            mock.patch.object(
                context, "has_permission_for_definition", side_effect=_mock_definition_ownership
            ),
            mock.patch.object(
                context, "was_permission_checked", side_effect=_mock_permission_check
            ),
        ):
            yield
