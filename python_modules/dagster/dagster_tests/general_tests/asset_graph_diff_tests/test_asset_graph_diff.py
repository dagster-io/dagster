import os
import sys
import time
from typing import List, Optional
from unittest import mock

import pytest
from dagster import DagsterInstance, asset, instance_for_test
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.host_representation.origin import InProcessCodeLocationOrigin
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._core.workspace.workspace import (
    CodeLocationEntry,
    CodeLocationLoadStatus,
)

from .asset_graphs.scenario_1 import defs as scenario_1_defs

defs_by_scenario = {"scenario_1": scenario_1_defs}


@pytest.fixture
def instance():
    with instance_for_test() as the_instance:
        yield the_instance


def _make_location_entry(scenario_name: str, instance: DagsterInstance):
    origin = InProcessCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            module_name=(
                f"dagster_tests.general_tests.asset_graph_diff_tests.asset_graphs.{scenario_name}"
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


def _make_context(instance: DagsterInstance, defs_attrs):
    return WorkspaceRequestContext(
        instance=mock.MagicMock(),
        workspace_snapshot={
            defs_attr: _make_location_entry(defs_attr, instance) for defs_attr in defs_attrs
        },
        process_context=mock.MagicMock(),
        version=None,
        source=None,
        read_only=True,
    )


def get_parent_deployment_graph_for_scenario(scenario):
    return ExternalAssetGraph.from_workspace(_make_context(instance, [scenario]))


def get_branch_deployment_graph_with_code_changes(
    scenario, new_assets: Optional[List] = None, updated_assets: Optional[List] = None
):
    scenario_defs_as_repo = defs_by_scenario[scenario].get_asset_graph()
    parent_assets_by_key = {
        asset.key: asset
        for asset in list(scenario_defs_as_repo.assets) + list(scenario_defs_as_repo.source_assets)
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


def compute_graph_diff(parent_graph: AssetGraph, branch_graph: AssetGraph):
    changes = {}
    for asset_key in branch_graph.all_asset_keys:
        if asset_key in parent_graph.all_asset_keys:
            all_changes = []
            if branch_graph.get_code_version(asset_key) != parent_graph.get_code_version(asset_key):
                all_changes.append("code_version")
            if branch_graph.get_parents(asset_key) != parent_graph.get_parents(asset_key):
                all_changes.append("inputs")
            changes[asset_key] = all_changes
        else:
            changes[asset_key] = ["new"]

    return changes


def test_new_asset(instance):
    parent_deployment_asset_graph = get_parent_deployment_graph_for_scenario("scenario_1")

    @asset
    def new_asset():
        return 1

    branch_deployment_asset_graph = get_branch_deployment_graph_with_code_changes(
        scenario="scenario_1", new_assets=[new_asset]
    )

    diff = compute_graph_diff(parent_deployment_asset_graph, branch_deployment_asset_graph)

    assert diff.get(new_asset.key) == ["new"]


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
