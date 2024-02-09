import os
import sys
import time
from typing import List, Optional
from unittest import mock

import pytest
from dagster import DagsterInstance, asset, instance_for_test
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.branch_changes import BranchChangeResolver, ChangeReason
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.host_representation.origin import InProcessCodeLocationOrigin
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._core.workspace.workspace import (
    CodeLocationEntry,
    CodeLocationLoadStatus,
)

from .parent_deployment_asset_graphs.basic_asset_graph import defs as basic_asset_graph

parent_deployment_defs_by_name = {"basic_asset_graph": basic_asset_graph}


@pytest.fixture
def instance():
    with instance_for_test() as the_instance:
        yield the_instance


def _make_location_entry(parent_graph_name: str, instance: DagsterInstance):
    origin = InProcessCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            module_name=(
                f"dagster_tests.general_tests.asset_graph_diff_tests.parent_deployment_asset_graphs.{parent_graph_name}"
            ),
            working_directory=os.getcwd(),
            attribute="defs",
        ),
        container_image=None,
        entry_point=None,
        container_context=None,
        location_name=None,
    )

    code_location = origin.create_location(instance)

    return CodeLocationEntry(
        origin=origin,
        code_location=code_location,
        load_error=None,
        load_status=CodeLocationLoadStatus.LOADED,
        display_metadata={},
        update_timestamp=time.time(),
    )


def _make_workspace_context(instance: DagsterInstance, parent_graph_names):
    return WorkspaceRequestContext(
        instance=mock.MagicMock(),
        workspace_snapshot={
            name: _make_location_entry(name, instance) for name in parent_graph_names
        },
        process_context=mock.MagicMock(),
        version=None,
        source=None,
        read_only=True,
    )


def _get_branch_deployment_graph_with_code_changes(
    parent_graph_name, new_assets: Optional[List] = None, updated_assets: Optional[List] = None
):
    """Applies the provided changes to a parent asset graph. We do this by getting the list of
    assets from the parent Definitions object and adding in the new_assets and replacing an
    updated_assets. Then we can make a new Definitions object and make an AssetGraph.
    """
    parent_asset_graph = parent_deployment_defs_by_name[parent_graph_name].get_asset_graph()
    parent_assets_by_key = {
        asset.key: asset
        for asset in list(parent_asset_graph.assets) + list(parent_asset_graph.source_assets)
    }
    new_assets = new_assets or []
    if updated_assets:
        for asset in updated_assets:
            if parent_assets_by_key.get(asset.key) is not None:
                del parent_assets_by_key[asset.key]
            else:
                assert False, "Asset included in updated_assets must exist as either an asset or a source asset in parent deployment"
    else:
        updated_assets = []
    return AssetGraph.from_assets(
        all_assets=new_assets + updated_assets + list(parent_assets_by_key.values())
    )


def get_branch_change_resolver_for_parent_graph(
    instance,
    parent_graph_name: str,
    new_assets: Optional[List] = None,
    updated_assets: Optional[List] = None,
):
    """Returns a subclass of BranchChangeResolver with some deployment-specific methods overwritten so that we can
    effectively run unit tests. In our tests we want to always be considered in a branch deployment, and
    the method for getting the parent asset graph is different than in a real branch deployment.
    """
    branch_graph = _get_branch_deployment_graph_with_code_changes(
        parent_graph_name=parent_graph_name, new_assets=new_assets, updated_assets=updated_assets
    )

    class TestingBranchChangeResolver(BranchChangeResolver):
        def _get_parent_deployment_asset_graph(self):
            return ExternalAssetGraph.from_workspace(
                _make_workspace_context(instance, [parent_graph_name])
            )

        def _is_branch_deployment(self) -> bool:
            # for testing, we want to always be in a branch deployment
            return True

    return TestingBranchChangeResolver(instance=instance, branch_asset_graph=branch_graph)


def test_new_asset(instance):
    @asset
    def new_asset():
        return 1

    resolver = get_branch_change_resolver_for_parent_graph(
        instance=instance, parent_graph_name="basic_asset_graph", new_assets=[new_asset]
    )

    assert resolver.is_changed_in_branch(new_asset.key)
    assert resolver.get_changes_for_asset(new_asset.key) == [ChangeReason.NEW]
    assert not resolver.is_changed_in_branch(AssetKey("upstream"))


"""
Scenarios to test:
* Adding a new asset to a graph, no connections to existing graph
* Adding a new asset to a graph with connections to existing graph
* Updating the code versions of existing assets in a graph
* Changing the inputs of an existing asset in a graph
* may need to do all of the above with different types of assets? This will depend on impl details
* One asset updated multiple ways (code version change and inputs change, etc) - should we get a list of
all changes, or should we return one and have a priority list, or say changed, but give no reason
* Change an asset, and then revert the change
* behavior of how we shoe changed assets after they've been materialized (need to figure out what this
change if any should be)
* if we do any caching, then need to test what happens when parent graph updates, or when multiple changes
are made in sequence to the branch deployment graph
* test at scale - generate a really large graph, may need to test various types of connectedness too if the
diff impl does graph traversal stuff instead of iteration through a list?
* if impl compares all codelocations as a group instead of each code location against it's parent version,
then need to test things like duplicate asset keys
* test a completely new definitions
"""
