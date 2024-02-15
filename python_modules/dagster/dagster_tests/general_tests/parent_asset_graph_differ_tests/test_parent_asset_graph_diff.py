import os
import sys
import time
from typing import List, Mapping
from unittest import mock

import pytest
from dagster import DagsterInstance, instance_for_test
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.parent_asset_graph_differ import ChangeReason, ParentAssetGraphDiffer
from dagster._core.definitions.repository_definition.valid_definitions import (
    SINGLETON_REPOSITORY_NAME,
)
from dagster._core.host_representation.origin import InProcessCodeLocationOrigin
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._core.workspace.workspace import (
    CodeLocationEntry,
    CodeLocationLoadStatus,
)


@pytest.fixture
def instance():
    with instance_for_test() as the_instance:
        yield the_instance


def _make_location_entry(scenario_name: str, definitions_file: str, instance: DagsterInstance):
    origin = InProcessCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            module_name=(
                f"dagster_tests.general_tests.parent_asset_graph_differ_tests.asset_graph_scenarios.{scenario_name}.{definitions_file}"
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


def _make_workspace_context(
    instance: DagsterInstance, scenario_to_definitions: Mapping[str, str]
) -> WorkspaceRequestContext:
    return WorkspaceRequestContext(
        instance=mock.MagicMock(),
        workspace_snapshot={
            scenario_name: _make_location_entry(scenario_name, definitions_file, instance)
            for scenario_name, definitions_file in scenario_to_definitions.items()
        },
        process_context=mock.MagicMock(),
        version=None,
        source=None,
        read_only=True,
    )


def get_parent_asset_graph_differ(
    instance,
    parent_code_locations: List[str],
    branch_code_location_to_definitions: Mapping[str, str],
    code_location_to_diff: str,
):
    """Returns a ParentAssetClassDiffer to compare a particular repository in a branch deployment to
    the corresponding repository in the parent deployment.

    For each deployment (parent and branch) we need to create a workspace context with a set of code locations in it.
    The folders in asset_graph_scenarios define various code locations. Each folder contains a parent_asset_graph.py file, which
    contains the Definitions object for the parent deployment. The remaining files in the folder (prefixed branch_deployment_*)
    are various modifications to the parent_asset_graph.py file, to represent branch deployments that may be opened against
    the parent deployment. To make the workspace for each deployment, we need a list of code locations to load in the parent deployment
    and a mapping of code location names to definitions file names to load the correct changes in the branch deployment. Finally, we
    need the name of the code location to compare between the branch deployment and parent deployment.

    Args:
        instance: A DagsterInstance
        parent_code_locations: List of code locations to load in the parent deployment
        branch_code_location_to_definitions: Mapping of code location to definitions file to load in the branch deployment
        code_location_to_diff: Name of the code location to compute differences between parent and branch deployments
    """
    branch_worksapce_ctx = _make_workspace_context(instance, branch_code_location_to_definitions)

    parent_worksapce_ctx = _make_workspace_context(
        instance, {code_location: "parent_asset_graph" for code_location in parent_code_locations}
    )

    return ParentAssetGraphDiffer.from_external_repositories(
        code_location_name=code_location_to_diff,
        repository_name=SINGLETON_REPOSITORY_NAME,
        branch_workspace=branch_worksapce_ctx,
        parent_workspace=parent_worksapce_ctx,
    )


def test_new_asset(instance):
    differ = get_parent_asset_graph_differ(
        instance=instance,
        code_location_to_diff="basic_asset_graph",
        parent_code_locations=["basic_asset_graph"],
        branch_code_location_to_definitions={"basic_asset_graph": "branch_deployment_new_asset"},
    )

    assert differ.get_changes_for_asset(AssetKey("new_asset")) == [ChangeReason.NEW]
    assert len(differ.get_changes_for_asset(AssetKey("upstream"))) == 0


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
