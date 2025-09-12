"""Test for definition-level ownership permissions in has_permission_for_asset_graph.

This test validates that asset operations respect definition ownership when the viewer
has owner permissions but only owns specific assets.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from unittest import mock

from dagster import AssetKey, Definitions, StaticPartitionsDefinition, asset
from dagster._core.instance import DagsterInstance
from dagster._core.test_utils import instance_for_test
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.client.query import LAUNCH_PARTITION_BACKFILL_MUTATION
from dagster_graphql.test.utils import define_out_of_process_context, execute_dagster_graphql

partitions_def = StaticPartitionsDefinition(["a", "b", "c"])


@asset(partitions_def=partitions_def)
def asset_A():
    return 1


@asset(partitions_def=partitions_def)
def asset_B():
    return 2


def get_test_repo():
    return Definitions(assets=[asset_A, asset_B]).get_repository_def()


@contextmanager
def define_context_with_owner_permissions(
    python_or_workspace_file: str,
    fn_name: str,
    instance: DagsterInstance,
    owned_assets: list[AssetKey],
) -> Iterator[WorkspaceRequestContext]:
    with define_out_of_process_context(
        python_or_workspace_file, fn_name, instance, read_only=True
    ) as context:
        with (
            mock.patch.object(context, "has_owner_permission", side_effect=lambda _: True),
            mock.patch.object(
                context,
                "is_viewer_definition_owner",
                side_effect=lambda node: node.key in owned_assets,
            ),
        ):
            yield context


def test_definition_owner_permissions():
    with instance_for_test() as instance:
        # Create a read-only context that gives us owner permissions but not global permissions
        with define_context_with_owner_permissions(
            __file__, "get_test_repo", instance, owned_assets=[AssetKey(["asset_A"])]
        ) as context:

            def launch_partition_backfill(asset_selection: list[AssetKey]):
                result = execute_dagster_graphql(
                    context,
                    LAUNCH_PARTITION_BACKFILL_MUTATION,
                    variables={
                        "backfillParams": {
                            "partitionNames": ["a", "b"],
                            "assetSelection": [key.to_graphql_input() for key in asset_selection],
                        }
                    },
                )
                assert result.data
                return result.data["launchPartitionBackfill"]["__typename"]

            assert launch_partition_backfill([AssetKey(["asset_A"])]) == "LaunchBackfillSuccess"
            assert launch_partition_backfill([AssetKey(["asset_B"])]) == "UnauthorizedError"
            assert (
                launch_partition_backfill([AssetKey(["asset_A"]), AssetKey(["asset_B"])])
                == "UnauthorizedError"
            )
