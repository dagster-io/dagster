import os
import sys
import time
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


def _make_location_entry(
    scenario_folder_name: str, definitions_file: str, instance: DagsterInstance
):
    origin = InProcessCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            module_name=(
                f"dagster_tests.general_tests.parent_asset_graph_differ_tests.asset_graph_scenarios.{scenario_folder_name}.{definitions_file}"
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
    instance: DagsterInstance, scenario_folder_name: str, definitions_file: str
) -> WorkspaceRequestContext:
    return WorkspaceRequestContext(
        instance=mock.MagicMock(),
        workspace_snapshot={
            scenario_folder_name: _make_location_entry(
                scenario_folder_name, definitions_file, instance
            )
        },
        process_context=mock.MagicMock(),
        version=None,
        source=None,
        read_only=True,
    )


def get_parent_asset_graph_differ(
    instance,
    scenario_name: str,
    parent_graph_file_name: str,
    branch_graph_file_name: str,
):
    """Returns a subclass of ParentAssetGraphDiffer with some deployment-specific methods overwritten so that we can
    effectively run unit tests. In our tests we want to always be considered in a branch deployment, and
    the method for getting the parent asset graph is different than in a real branch deployment.
    """
    branch_worksapce_ctx = _make_workspace_context(instance, scenario_name, branch_graph_file_name)

    parent_worksapce_ctx = _make_workspace_context(instance, scenario_name, parent_graph_file_name)

    return ParentAssetGraphDiffer.from_external_repositories(
        code_location_name=scenario_name,
        repository_name=SINGLETON_REPOSITORY_NAME,
        branch_workspace=branch_worksapce_ctx,
        parent_workspace=parent_worksapce_ctx,
    )


def test_new_asset(instance):
    differ = get_parent_asset_graph_differ(
        instance=instance,
        scenario_name="basic_asset_graph",
        parent_graph_file_name="parent_asset_graph",
        branch_graph_file_name="branch_deployment_new_asset",
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
