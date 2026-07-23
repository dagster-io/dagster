import unittest.mock
import warnings

import dagster as dg
import pytest
from dagster._core.definitions.asset_key import AssetJobKey
from dagster._core.definitions.assets.graph.remote_asset_graph import RemoteAssetJobNode
from dagster._core.remote_representation.code_location import CodeLocation
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._core.workspace.workspace import CodeLocationEntry, CurrentWorkspace


@dg.asset
def asset_a():
    return 1


@dg.asset(partitions_def=dg.StaticPartitionsDefinition(["x", "y"]))
def partitioned_asset():
    return 1


@dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2024-01-01"))
def daily_partitioned_asset():
    return 1


conditioned_job = dg.define_asset_job(
    name="conditioned_job",
    selection=[asset_a],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.eager()
    ),
)
unconditioned_job = dg.define_asset_job(name="unconditioned_job", selection=[asset_a])
partitioned_job = dg.define_asset_job(
    name="partitioned_job",
    selection=[partitioned_asset],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.eager()
    ),
)
daily_partitioned_job = dg.define_asset_job(
    name="daily_partitioned_job",
    selection=[daily_partitioned_asset],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.eager()
    ),
)

defs = dg.Definitions(
    assets=[asset_a, partitioned_asset, daily_partitioned_asset],
    jobs=[conditioned_job, unconditioned_job, partitioned_job, daily_partitioned_job],
)


def _remote_repo(defer_snapshots: bool) -> RemoteRepository:
    return RemoteRepository(
        RepositorySnap.from_def(defs.get_repository_def(), defer_snapshots=defer_snapshots),
        repository_handle=RepositoryHandle.for_test(
            location_name="foo_location", repository_name="bar_repo"
        ),
        auto_materialize_use_sensors=True,
        # only consulted when a deferred full snapshot is actually fetched; job entity
        # nodes must be buildable from the refs alone, without triggering this
        ref_to_data_fn=_fail_on_fetch if defer_snapshots else None,
    )


def _fail_on_fetch(ref):
    raise AssertionError(f"unexpectedly fetched full snapshot for {ref.name}")


# defer_snapshots=False ships full JobSnaps (job_datas); True ships JobRefSnaps (job_refs).
# Job entity nodes must be built identically from either.
@pytest.mark.parametrize("defer_snapshots", [False, True], ids=["job_datas", "job_refs"])
def test_remote_graph_builds_asset_job_nodes(defer_snapshots: bool) -> None:
    graph = _remote_repo(defer_snapshots).asset_graph

    assert graph.has(AssetJobKey("conditioned_job"))
    assert not graph.has(AssetJobKey("unconditioned_job"))

    node = graph.get(AssetJobKey("conditioned_job"))
    assert isinstance(node, RemoteAssetJobNode)
    assert node.automation_condition is not None
    assert node.partitions_def is None

    # the graph resolves the job's selected asset keys from its job_names reverse mapping
    assert graph.asset_keys_for_job("conditioned_job") == {dg.AssetKey("asset_a")}

    # the node carries the repository handle (needed to route run submission)
    assert node.handle.repository_name == "bar_repo"


# partitions_def comes from the repository's partition sets (not the JobSnap); it must
# reconstruct equivalently for time-window and static defs, from either snapshot mode.
@pytest.mark.parametrize("defer_snapshots", [False, True], ids=["job_datas", "job_refs"])
@pytest.mark.parametrize(
    "job_name,expected_partitions_def",
    [
        ("partitioned_job", dg.StaticPartitionsDefinition(["x", "y"])),
        ("daily_partitioned_job", dg.DailyPartitionsDefinition(start_date="2024-01-01")),
    ],
    ids=["static", "daily"],
)
def test_remote_job_node_resolves_partitions_def(
    defer_snapshots: bool, job_name: str, expected_partitions_def
) -> None:
    graph = _remote_repo(defer_snapshots).asset_graph

    node = graph.get(AssetJobKey(job_name))
    assert node.partitions_def is not None
    assert node.partitions_def == expected_partitions_def


def _conditioned_defs(asset_name: str, job_name: str) -> dg.Definitions:
    @dg.asset(name=asset_name)
    def _asset():
        return 1

    job = dg.define_asset_job(
        name=job_name,
        selection=[_asset],
        automation_condition=dg.AutomationCondition.all_job_root_assets_match(
            dg.AutomationCondition.eager()
        ),
    )
    return dg.Definitions(assets=[_asset], jobs=[job])


def _workspace_with_locations(defs_by_location: dict[str, dg.Definitions]) -> CurrentWorkspace:
    entries = {}
    for location_name, defs in defs_by_location.items():
        repo_def = defs.get_repository_def()
        remote_repo = RemoteRepository(
            RepositorySnap.from_def(repo_def),
            repository_handle=RepositoryHandle.for_test(
                location_name=location_name, repository_name=repo_def.name
            ),
            auto_materialize_use_sensors=True,
        )
        mock_location = unittest.mock.MagicMock(spec=CodeLocation)
        mock_location.name = location_name
        mock_location.get_repositories.return_value = {remote_repo.name: remote_repo}
        mock_entry = unittest.mock.MagicMock(spec=CodeLocationEntry)
        type(mock_entry).code_location = unittest.mock.PropertyMock(return_value=mock_location)
        entries[location_name] = mock_entry
    return CurrentWorkspace(code_location_entries=entries)


# AssetJobKey is just the bare job name, so a conditioned job with the same name in two code
# locations collides on merge (last-wins). Distinct names never collide.
@pytest.mark.parametrize(
    "second_job_name, expect_warning",
    [("shared_job", True), ("other_job", False)],
    ids=["same_name_collides", "distinct_names_ok"],
)
def test_duplicate_job_keys_across_locations(second_job_name: str, expect_warning: bool) -> None:
    workspace = _workspace_with_locations(
        {
            "location_one": _conditioned_defs(asset_name="a1", job_name="shared_job"),
            "location_two": _conditioned_defs(asset_name="a2", job_name=second_job_name),
        }
    )

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        graph = workspace.asset_graph

    job_key_warnings = [
        w for w in records if "same job name in multiple code locations" in str(w.message)
    ]
    assert bool(job_key_warnings) is expect_warning

    # regardless of the collision, each distinct job name resolves to a single node (last-wins)
    assert graph.has(AssetJobKey("shared_job"))
    assert graph.has(AssetJobKey(second_job_name))
