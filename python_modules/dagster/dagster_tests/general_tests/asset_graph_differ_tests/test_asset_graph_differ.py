import os
import sys
import time
from collections.abc import Mapping
from unittest import mock

import dagster as dg
import pytest
from dagster import DagsterInstance
from dagster._core.definitions.assets.graph.asset_graph_differ import (
    AssetDefinitionChangeType,
    AssetDefinitionDiffDetails,
    AssetGraphDiffer,
    DictDiff,
    ValueDiff,
)
from dagster._core.definitions.repository_definition.valid_definitions import (
    SINGLETON_REPOSITORY_NAME,
)
from dagster._core.remote_origin import InProcessCodeLocationOrigin
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._core.workspace.workspace import (
    CodeLocationEntry,
    CodeLocationLoadStatus,
    CurrentWorkspace,
)


@pytest.fixture
def instance():
    with dg.instance_for_test() as the_instance:
        yield the_instance


def _make_location_entry(scenario_name: str, definitions_file: str, instance: DagsterInstance):
    origin = InProcessCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            module_name=(
                f"dagster_tests.general_tests.asset_graph_differ_tests.asset_graph_scenarios.{scenario_name}.{definitions_file}"
            ),
            working_directory=os.getcwd(),
            attribute="defs",
        ),
        container_image=None,
        entry_point=None,
        container_context=None,
        location_name=scenario_name,
    )

    code_location = origin.create_location(instance)

    return CodeLocationEntry(
        origin=origin,
        code_location=code_location,
        load_error=None,
        load_status=CodeLocationLoadStatus.LOADED,
        display_metadata={},
        update_timestamp=time.time(),
        version_key="test",
    )


def _make_workspace_context(
    instance: DagsterInstance, scenario_to_definitions: Mapping[str, str]
) -> WorkspaceRequestContext:
    return WorkspaceRequestContext(
        instance=mock.MagicMock(),
        current_workspace=CurrentWorkspace(
            code_location_entries={
                scenario_name: _make_location_entry(scenario_name, definitions_file, instance)
                for scenario_name, definitions_file in scenario_to_definitions.items()
            },
            instance=instance,
        ),
        process_context=mock.MagicMock(),
        version=None,
        source=None,
        read_only=True,
    )


def get_asset_graph_differ(
    instance,
    base_code_locations: list[str],
    branch_code_location_to_definitions: Mapping[str, str],
    code_location_to_diff: str,
) -> AssetGraphDiffer:
    """Returns an AssetGraphDiffer to compare a particular repository in a branch deployment to
    the corresponding repository in the base deployment.

    For each deployment (base and branch) we need to create a workspace context with a set of code locations in it.
    The folders in asset_graph_scenarios define various code locations. Each folder contains a base_asset_graph.py file, which
    contains the Definitions object for the base deployment. The remaining files in the folder (prefixed branch_deployment_*)
    are various modifications to the base_asset_graph.py file, to represent branch deployments that may be opened against
    the base deployment. To make the workspace for each deployment, we need a list of code locations to load in the base deployment
    and a mapping of code location names to definitions file names to load the correct changes in the branch deployment. Finally, we
    need the name of the code location to compare between the branch deployment and base deployment.

    Args:
        instance: A DagsterInstance
        base_code_locations: List of code locations to load in the base deployment
        branch_code_location_to_definitions: Mapping of code location to definitions file to load in the branch deployment
        code_location_to_diff: Name of the code location to compute differences between base and branch deployments
    """
    branch_workspace_ctx = _make_workspace_context(instance, branch_code_location_to_definitions)

    base_workspace_ctx = _make_workspace_context(
        instance, {code_location: "base_asset_graph" for code_location in base_code_locations}
    )

    if code_location_to_diff:
        branch_asset_graph = (
            branch_workspace_ctx.get_code_location(code_location_to_diff)
            .get_repository(SINGLETON_REPOSITORY_NAME)
            .asset_graph
        )
        base_asset_graph = (
            (
                base_workspace_ctx.get_code_location(code_location_to_diff)
                .get_repository(SINGLETON_REPOSITORY_NAME)
                .asset_graph
            )
            if base_workspace_ctx.has_code_location(code_location_to_diff)
            else None
        )
    else:
        branch_asset_graph = branch_workspace_ctx.asset_graph
        base_asset_graph = base_workspace_ctx.asset_graph

    return AssetGraphDiffer(
        branch_asset_graph=branch_asset_graph,
        base_asset_graph=base_asset_graph,
    )


@pytest.mark.parametrize("code_location_to_diff", [None, "basic_asset_graph"])
def test_new_asset(instance, code_location_to_diff):
    differ = get_asset_graph_differ(
        instance=instance,
        code_location_to_diff=code_location_to_diff,
        base_code_locations=["basic_asset_graph"],
        branch_code_location_to_definitions={"basic_asset_graph": "branch_deployment_new_asset"},
    )

    assert differ.get_changes_for_asset(dg.AssetKey("new_asset")) == [AssetDefinitionChangeType.NEW]
    assert len(differ.get_changes_for_asset(dg.AssetKey("upstream"))) == 0
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("new_asset")
    ) == AssetDefinitionDiffDetails(change_types={AssetDefinitionChangeType.NEW})
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("upstream")
    ) == AssetDefinitionDiffDetails(change_types=set())


@pytest.mark.parametrize("code_location_to_diff", [None, "basic_asset_graph"])
def test_removed_asset(instance, code_location_to_diff) -> None:
    differ = get_asset_graph_differ(
        instance=instance,
        code_location_to_diff=code_location_to_diff,
        base_code_locations=["basic_asset_graph"],
        branch_code_location_to_definitions={
            "basic_asset_graph": "branch_deployment_removed_asset"
        },
    )

    assert differ.get_changes_for_asset(dg.AssetKey("downstream")) == [
        AssetDefinitionChangeType.REMOVED
    ]
    assert len(differ.get_changes_for_asset(dg.AssetKey("upstream"))) == 0
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("downstream")
    ) == AssetDefinitionDiffDetails(change_types={AssetDefinitionChangeType.REMOVED})
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("upstream")
    ) == AssetDefinitionDiffDetails(change_types=set())


@pytest.mark.parametrize("code_location_to_diff", [None, "basic_asset_graph"])
def test_new_asset_connected(instance, code_location_to_diff):
    differ = get_asset_graph_differ(
        instance=instance,
        code_location_to_diff=code_location_to_diff,
        base_code_locations=["basic_asset_graph"],
        branch_code_location_to_definitions={
            "basic_asset_graph": "branch_deployment_new_asset_connected"
        },
    )

    assert differ.get_changes_for_asset(dg.AssetKey("new_asset")) == [AssetDefinitionChangeType.NEW]
    assert differ.get_changes_for_asset(dg.AssetKey("downstream")) == [
        AssetDefinitionChangeType.DEPENDENCIES
    ]
    assert len(differ.get_changes_for_asset(dg.AssetKey("upstream"))) == 0
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("new_asset")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.NEW},
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("downstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.DEPENDENCIES},
        dependencies=DictDiff(
            added_keys={dg.AssetKey("new_asset")}, changed_keys=set(), removed_keys=set()
        ),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("upstream")
    ) == AssetDefinitionDiffDetails(change_types=set())


@pytest.mark.parametrize("code_location_to_diff", [None, "code_versions_asset_graph"])
def test_update_code_version(instance, code_location_to_diff):
    differ = get_asset_graph_differ(
        instance=instance,
        code_location_to_diff=code_location_to_diff,
        base_code_locations=["code_versions_asset_graph"],
        branch_code_location_to_definitions={
            "code_versions_asset_graph": "branch_deployment_update_code_version"
        },
    )

    assert differ.get_changes_for_asset(dg.AssetKey("upstream")) == [
        AssetDefinitionChangeType.CODE_VERSION
    ]
    assert len(differ.get_changes_for_asset(dg.AssetKey("downstream"))) == 0
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("upstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.CODE_VERSION},
        code_version=ValueDiff(old="1", new="2"),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("downstream")
    ) == AssetDefinitionDiffDetails(change_types=set())


@pytest.mark.parametrize("code_location_to_diff", [None, "basic_asset_graph"])
def test_change_inputs(instance, code_location_to_diff):
    differ = get_asset_graph_differ(
        instance=instance,
        code_location_to_diff=code_location_to_diff,
        base_code_locations=["basic_asset_graph"],
        branch_code_location_to_definitions={
            "basic_asset_graph": "branch_deployment_change_inputs"
        },
    )

    assert differ.get_changes_for_asset(dg.AssetKey("downstream")) == [
        AssetDefinitionChangeType.DEPENDENCIES
    ]
    assert len(differ.get_changes_for_asset(dg.AssetKey("upstream"))) == 0
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("downstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.DEPENDENCIES},
        dependencies=DictDiff(
            added_keys=set(), changed_keys=set(), removed_keys={dg.AssetKey("upstream")}
        ),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("upstream")
    ) == AssetDefinitionDiffDetails(change_types=set())


@pytest.mark.parametrize("code_location_to_diff", [None, "code_versions_asset_graph"])
def test_multiple_changes_for_one_asset(instance, code_location_to_diff):
    differ = get_asset_graph_differ(
        instance=instance,
        code_location_to_diff=code_location_to_diff,
        base_code_locations=["code_versions_asset_graph"],
        branch_code_location_to_definitions={
            "code_versions_asset_graph": "branch_deployment_multiple_changes"
        },
    )

    assert set(differ.get_changes_for_asset(dg.AssetKey("downstream"))) == {
        AssetDefinitionChangeType.CODE_VERSION,
        AssetDefinitionChangeType.DEPENDENCIES,
    }
    assert len(differ.get_changes_for_asset(dg.AssetKey("upstream"))) == 0
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("downstream")
    ) == AssetDefinitionDiffDetails(
        change_types={
            AssetDefinitionChangeType.DEPENDENCIES,
            AssetDefinitionChangeType.CODE_VERSION,
        },
        code_version=ValueDiff(old="1", new="2"),
        dependencies=DictDiff(
            added_keys=set(), changed_keys=set(), removed_keys={dg.AssetKey("upstream")}
        ),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("upstream")
    ) == AssetDefinitionDiffDetails(change_types=set())


@pytest.mark.parametrize("code_location_to_diff", [None, "code_versions_asset_graph"])
def test_change_then_revert(instance, code_location_to_diff):
    differ = get_asset_graph_differ(
        instance=instance,
        code_location_to_diff=code_location_to_diff,
        base_code_locations=["code_versions_asset_graph"],
        branch_code_location_to_definitions={
            "code_versions_asset_graph": "branch_deployment_update_code_version"
        },
    )

    assert differ.get_changes_for_asset(dg.AssetKey("upstream")) == [
        AssetDefinitionChangeType.CODE_VERSION
    ]
    assert len(differ.get_changes_for_asset(dg.AssetKey("downstream"))) == 0
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("upstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.CODE_VERSION},
        code_version=ValueDiff(old="1", new="2"),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("downstream")
    ) == AssetDefinitionDiffDetails(change_types=set())

    differ = get_asset_graph_differ(
        instance=instance,
        code_location_to_diff="code_versions_asset_graph",
        base_code_locations=["code_versions_asset_graph"],
        branch_code_location_to_definitions={"code_versions_asset_graph": "base_asset_graph"},
    )

    assert len(differ.get_changes_for_asset(dg.AssetKey("upstream"))) == 0
    assert len(differ.get_changes_for_asset(dg.AssetKey("downstream"))) == 0
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("upstream")
    ) == AssetDefinitionDiffDetails(change_types=set())
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("downstream")
    ) == AssetDefinitionDiffDetails(change_types=set())


@pytest.mark.parametrize("code_location_to_diff", [None, "huge_asset_graph"])
def test_large_asset_graph(instance, code_location_to_diff):
    differ = get_asset_graph_differ(
        instance=instance,
        code_location_to_diff=code_location_to_diff,
        base_code_locations=["huge_asset_graph"],
        branch_code_location_to_definitions={
            "huge_asset_graph": "branch_deployment_restructure_graph"
        },
    )

    for i in range(6, 1000):
        key = dg.AssetKey(f"asset_{i}")
        assert differ.get_changes_for_asset(key) == [AssetDefinitionChangeType.DEPENDENCIES]
        assert differ.get_changes_for_asset_with_diff(key).change_types == {
            AssetDefinitionChangeType.DEPENDENCIES
        }

    for i in range(6):
        key = dg.AssetKey(f"asset_{i}")
        assert len(differ.get_changes_for_asset(key)) == 0
        assert differ.get_changes_for_asset_with_diff(key) == AssetDefinitionDiffDetails(
            change_types=set()
        )


@pytest.mark.parametrize("code_location_to_diff", [None, "basic_asset_graph"])
def test_multiple_code_locations(instance, code_location_to_diff):
    # There are duplicate asset keys in the asset graphs of basic_asset_graph and code_versions_asset_graph
    # this test ensures that the AssetGraphDiffer constructs AssetGraphs of the intended code location and does not
    # include assets from other code locations
    differ = get_asset_graph_differ(
        instance=instance,
        code_location_to_diff=code_location_to_diff,
        base_code_locations=["basic_asset_graph", "code_versions_asset_graph"],
        branch_code_location_to_definitions={
            "basic_asset_graph": "branch_deployment_new_asset_connected"
        },
    )

    # if the code_versions_asset_graph were in the diff computation, ChangeReason.CODE_VERSION would be in the list
    assert differ.get_changes_for_asset(dg.AssetKey("new_asset")) == [AssetDefinitionChangeType.NEW]
    assert differ.get_changes_for_asset(dg.AssetKey("downstream")) == [
        AssetDefinitionChangeType.DEPENDENCIES
    ]
    assert len(differ.get_changes_for_asset(dg.AssetKey("upstream"))) == 0
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("new_asset")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.NEW},
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("downstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.DEPENDENCIES},
        dependencies=DictDiff(
            added_keys={dg.AssetKey("new_asset")}, changed_keys=set(), removed_keys=set()
        ),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("upstream")
    ) == AssetDefinitionDiffDetails(change_types=set())


@pytest.mark.parametrize("code_location_to_diff", [None, "basic_asset_graph"])
def test_new_code_location(instance, code_location_to_diff):
    differ = get_asset_graph_differ(
        instance=instance,
        code_location_to_diff=code_location_to_diff,
        base_code_locations=[],
        branch_code_location_to_definitions={"basic_asset_graph": "branch_deployment_new_asset"},
    )
    assert differ.get_changes_for_asset(dg.AssetKey("new_asset")) == [AssetDefinitionChangeType.NEW]
    assert differ.get_changes_for_asset(dg.AssetKey("upstream")) == [AssetDefinitionChangeType.NEW]
    assert differ.get_changes_for_asset(dg.AssetKey("downstream")) == [
        AssetDefinitionChangeType.NEW
    ]
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("new_asset")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.NEW},
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("upstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.NEW},
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("downstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.NEW},
    )


@pytest.mark.parametrize("code_location_to_diff", [None, "partitioned_asset_graph"])
def test_change_partitions_definitions(instance, code_location_to_diff):
    differ = get_asset_graph_differ(
        instance=instance,
        code_location_to_diff=code_location_to_diff,
        base_code_locations=["partitioned_asset_graph"],
        branch_code_location_to_definitions={
            "partitioned_asset_graph": "branch_deployment_change_partitions_def"
        },
    )
    assert differ.get_changes_for_asset(dg.AssetKey("daily_upstream")) == [
        AssetDefinitionChangeType.PARTITIONS_DEFINITION
    ]
    assert differ.get_changes_for_asset(dg.AssetKey("daily_downstream")) == [
        AssetDefinitionChangeType.PARTITIONS_DEFINITION
    ]
    assert differ.get_changes_for_asset(dg.AssetKey("static_upstream")) == [
        AssetDefinitionChangeType.PARTITIONS_DEFINITION
    ]
    assert differ.get_changes_for_asset(dg.AssetKey("static_downstream")) == [
        AssetDefinitionChangeType.PARTITIONS_DEFINITION
    ]
    assert differ.get_changes_for_asset(dg.AssetKey("multi_partitioned_upstream")) == [
        AssetDefinitionChangeType.PARTITIONS_DEFINITION
    ]
    assert differ.get_changes_for_asset(dg.AssetKey("multi_partitioned_downstream")) == [
        AssetDefinitionChangeType.PARTITIONS_DEFINITION
    ]
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("daily_upstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.PARTITIONS_DEFINITION},
        partitions_definition=ValueDiff(
            old="TimeWindowPartitionsDefinition", new="TimeWindowPartitionsDefinition"
        ),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("daily_downstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.PARTITIONS_DEFINITION},
        partitions_definition=ValueDiff(
            old="TimeWindowPartitionsDefinition", new="TimeWindowPartitionsDefinition"
        ),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("static_upstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.PARTITIONS_DEFINITION},
        partitions_definition=ValueDiff(
            old="StaticPartitionsDefinition", new="StaticPartitionsDefinition"
        ),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("static_downstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.PARTITIONS_DEFINITION},
        partitions_definition=ValueDiff(
            old="StaticPartitionsDefinition", new="StaticPartitionsDefinition"
        ),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("multi_partitioned_upstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.PARTITIONS_DEFINITION},
        partitions_definition=ValueDiff(
            old="MultiPartitionsDefinition", new="MultiPartitionsDefinition"
        ),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("multi_partitioned_downstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.PARTITIONS_DEFINITION},
        partitions_definition=ValueDiff(
            old="MultiPartitionsDefinition", new="MultiPartitionsDefinition"
        ),
    )


@pytest.mark.parametrize("code_location_to_diff", [None, "partitioned_asset_graph"])
def test_change_partition_mapping(instance, code_location_to_diff):
    differ = get_asset_graph_differ(
        instance=instance,
        code_location_to_diff=code_location_to_diff,
        base_code_locations=["partitioned_asset_graph"],
        branch_code_location_to_definitions={
            "partitioned_asset_graph": "branch_deployment_change_partition_mappings"
        },
    )
    assert len(differ.get_changes_for_asset(dg.AssetKey("daily_upstream"))) == 0
    assert differ.get_changes_for_asset(dg.AssetKey("daily_downstream")) == [
        AssetDefinitionChangeType.DEPENDENCIES
    ]
    assert len(differ.get_changes_for_asset(dg.AssetKey("static_upstream"))) == 0
    assert differ.get_changes_for_asset(dg.AssetKey("static_downstream")) == [
        AssetDefinitionChangeType.DEPENDENCIES
    ]
    assert len(differ.get_changes_for_asset(dg.AssetKey("multi_partitioned_upstream"))) == 0
    assert differ.get_changes_for_asset(dg.AssetKey("multi_partitioned_downstream")) == [
        AssetDefinitionChangeType.DEPENDENCIES
    ]
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("daily_upstream")
    ) == AssetDefinitionDiffDetails(change_types=set())
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("daily_downstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.DEPENDENCIES},
        dependencies=DictDiff(
            added_keys=set(), changed_keys={dg.AssetKey("daily_upstream")}, removed_keys=set()
        ),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("static_upstream")
    ) == AssetDefinitionDiffDetails(change_types=set())
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("static_downstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.DEPENDENCIES},
        dependencies=DictDiff(
            added_keys=set(), changed_keys={dg.AssetKey("static_upstream")}, removed_keys=set()
        ),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("multi_partitioned_upstream")
    ) == AssetDefinitionDiffDetails(change_types=set())
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("multi_partitioned_downstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.DEPENDENCIES},
        dependencies=DictDiff(
            added_keys=set(),
            changed_keys={dg.AssetKey("multi_partitioned_upstream")},
            removed_keys=set(),
        ),
    )


@pytest.mark.parametrize("code_location_to_diff", [None, "tags_asset_graph"])
def test_change_tags(instance, code_location_to_diff):
    differ = get_asset_graph_differ(
        instance=instance,
        code_location_to_diff=code_location_to_diff,
        base_code_locations=["tags_asset_graph"],
        branch_code_location_to_definitions={"tags_asset_graph": "branch_deployment_change_tags"},
    )
    assert differ.get_changes_for_asset(dg.AssetKey("upstream")) == [AssetDefinitionChangeType.TAGS]
    assert differ.get_changes_for_asset(dg.AssetKey("downstream")) == [
        AssetDefinitionChangeType.TAGS
    ]
    assert differ.get_changes_for_asset(dg.AssetKey("fruits")) == [AssetDefinitionChangeType.TAGS]
    assert differ.get_changes_for_asset(dg.AssetKey("letters")) == [AssetDefinitionChangeType.TAGS]
    assert len(differ.get_changes_for_asset(dg.AssetKey("numbers"))) == 0
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("upstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.TAGS},
        tags=DictDiff(added_keys=set(), changed_keys=set(), removed_keys={"one"}),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("downstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.TAGS},
        tags=DictDiff(added_keys=set(), changed_keys={"baz"}, removed_keys=set()),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("fruits")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.TAGS},
        tags=DictDiff(added_keys={"green"}, changed_keys=set(), removed_keys={"red"}),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("letters")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.TAGS},
        tags=DictDiff(added_keys={"c"}, changed_keys=set(), removed_keys=set()),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("numbers")
    ) == AssetDefinitionDiffDetails(change_types=set())


@pytest.mark.parametrize("code_location_to_diff", [None, "metadata_asset_graph"])
def test_change_metadata(instance, code_location_to_diff):
    differ = get_asset_graph_differ(
        instance=instance,
        code_location_to_diff=code_location_to_diff,
        base_code_locations=["metadata_asset_graph"],
        branch_code_location_to_definitions={
            "metadata_asset_graph": "branch_deployment_change_metadata"
        },
    )
    assert differ.get_changes_for_asset(dg.AssetKey("upstream")) == [
        AssetDefinitionChangeType.METADATA
    ]
    assert differ.get_changes_for_asset(dg.AssetKey("downstream")) == [
        AssetDefinitionChangeType.METADATA
    ]
    assert differ.get_changes_for_asset(dg.AssetKey("fruits")) == [
        AssetDefinitionChangeType.METADATA
    ]
    assert differ.get_changes_for_asset(dg.AssetKey("letters")) == [
        AssetDefinitionChangeType.METADATA
    ]
    assert len(differ.get_changes_for_asset(dg.AssetKey("numbers"))) == 0
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("upstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.METADATA},
        metadata=DictDiff(
            added_keys=set(),
            changed_keys=set(),
            removed_keys={"one"},
        ),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("downstream")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.METADATA},
        metadata=DictDiff(
            added_keys=set(),
            changed_keys={"baz"},
            removed_keys=set(),
        ),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("fruits")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.METADATA},
        metadata=DictDiff(
            added_keys={"green"},
            changed_keys=set(),
            removed_keys={"red"},
        ),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("letters")
    ) == AssetDefinitionDiffDetails(
        change_types={AssetDefinitionChangeType.METADATA},
        metadata=DictDiff(
            added_keys={"c"},
            changed_keys=set(),
            removed_keys=set(),
        ),
    )
    assert differ.get_changes_for_asset_with_diff(
        dg.AssetKey("numbers")
    ) == AssetDefinitionDiffDetails(change_types=set())
