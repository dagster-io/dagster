import os
import sys
import time
from unittest import mock

from dagster import (
    AssetIn,
    AssetKey,
    DailyPartitionsDefinition,
    Definitions,
    IdentityPartitionMapping,
    SourceAsset,
    StaticPartitionMapping,
    StaticPartitionsDefinition,
    asset,
)
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.host_representation import InProcessCodeLocationOrigin
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._core.workspace.workspace import (
    CodeLocationEntry,
    CodeLocationLoadStatus,
)


@asset
def asset1():
    ...


defs1 = Definitions(assets=[asset1])


@asset
def asset2():
    ...


defs2 = Definitions(assets=[asset2])


asset1_source = SourceAsset("asset1")


@asset
def downstream(asset1):
    del asset1


downstream_defs = Definitions(assets=[asset1_source, downstream])


@asset(non_argument_deps={"asset1"})
def downstream_non_arg_dep():
    ...


downstream_defs_no_source = Definitions(assets=[downstream_non_arg_dep])

partitioned_source = SourceAsset(
    "partitioned_source", partitions_def=DailyPartitionsDefinition(start_date="2022-01-01")
)


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"),
    non_argument_deps={"partitioned_source"},
    auto_materialize_policy=AutoMaterializePolicy(
        on_missing=True,
        for_freshness=True,
        on_new_parent_data=True,
        time_window_partition_scope_minutes=(24 + 7) * 60,
    ),
)
def downstream_of_partitioned_source():
    pass


partitioned_defs = Definitions(assets=[partitioned_source, downstream_of_partitioned_source])

static_partition = partitions_def = StaticPartitionsDefinition(["foo", "bar"])


@asset(
    partitions_def=static_partition,
)
def static_partitioned_asset():
    pass


@asset(
    partitions_def=static_partition,
)
def other_static_partitioned_asset():
    pass


different_partitions_defs = Definitions(
    assets=[
        static_partitioned_asset,
        other_static_partitioned_asset,
        downstream_of_partitioned_source,
        partitioned_source,
    ]
)


def make_location_entry(defs_attr: str):
    origin = InProcessCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            python_file=__file__,
            working_directory=os.path.dirname(__file__),
            attribute=defs_attr,
        ),
        container_image=None,
        entry_point=None,
        container_context=None,
        location_name=None,
    )

    code_location = origin.create_location()

    return CodeLocationEntry(
        origin=origin,
        code_location=code_location,
        load_error=None,
        load_status=CodeLocationLoadStatus.LOADED,
        display_metadata={},
        update_timestamp=time.time(),
    )


def make_context(defs_attrs):
    return WorkspaceRequestContext(
        instance=mock.MagicMock(),
        workspace_snapshot={defs_attr: make_location_entry(defs_attr) for defs_attr in defs_attrs},
        process_context=mock.MagicMock(),
        version=None,
        source=None,
        read_only=True,
    )


def test_get_repository_handle():
    asset_graph = ExternalAssetGraph.from_workspace(make_context(["defs1", "defs2"]))

    assert asset_graph.get_materialization_job_names(asset1.key) == ["__ASSET_JOB"]
    repo_handle1 = asset_graph.get_repository_handle(asset1.key)
    assert repo_handle1.repository_name == "__repository__"
    assert repo_handle1.repository_python_origin.code_pointer.fn_name == "defs1"

    assert asset_graph.get_materialization_job_names(asset1.key) == ["__ASSET_JOB"]
    repo_handle2 = asset_graph.get_repository_handle(asset2.key)
    assert repo_handle2.repository_name == "__repository__"
    assert repo_handle2.repository_python_origin.code_pointer.fn_name == "defs2"


def test_cross_repo_dep_with_source_asset():
    asset_graph = ExternalAssetGraph.from_workspace(make_context(["defs1", "downstream_defs"]))
    assert len(asset_graph.source_asset_keys) == 0
    assert asset_graph.get_parents(AssetKey("downstream")) == {AssetKey("asset1")}
    assert asset_graph.get_children(AssetKey("asset1")) == {AssetKey("downstream")}
    assert (
        asset_graph.get_repository_handle(
            AssetKey("asset1")
        ).repository_python_origin.code_pointer.fn_name
        == "defs1"
    )
    assert asset_graph.get_materialization_job_names(AssetKey("asset1")) == ["__ASSET_JOB"]
    assert (
        asset_graph.get_repository_handle(
            AssetKey("downstream")
        ).repository_python_origin.code_pointer.fn_name
        == "downstream_defs"
    )
    assert asset_graph.get_materialization_job_names(AssetKey("downstream")) == ["__ASSET_JOB"]


def test_cross_repo_dep_no_source_asset():
    asset_graph = ExternalAssetGraph.from_workspace(
        make_context(["defs1", "downstream_defs_no_source"])
    )
    assert len(asset_graph.source_asset_keys) == 0
    assert asset_graph.get_parents(AssetKey("downstream_non_arg_dep")) == {AssetKey("asset1")}
    assert asset_graph.get_children(AssetKey("asset1")) == {AssetKey("downstream_non_arg_dep")}
    assert (
        asset_graph.get_repository_handle(
            AssetKey("asset1")
        ).repository_python_origin.code_pointer.fn_name
        == "defs1"
    )
    assert asset_graph.get_materialization_job_names(AssetKey("asset1")) == ["__ASSET_JOB"]
    assert (
        asset_graph.get_repository_handle(
            AssetKey("downstream_non_arg_dep")
        ).repository_python_origin.code_pointer.fn_name
        == "downstream_defs_no_source"
    )
    assert asset_graph.get_materialization_job_names(AssetKey("downstream_non_arg_dep")) == [
        "__ASSET_JOB"
    ]


def test_partitioned_source_asset():
    asset_graph = ExternalAssetGraph.from_workspace(make_context(["partitioned_defs"]))

    assert asset_graph.is_partitioned(AssetKey("partitioned_source"))
    assert asset_graph.is_partitioned(AssetKey("downstream_of_partitioned_source"))


def test_get_implicit_job_name_for_assets():
    asset_graph = ExternalAssetGraph.from_workspace(make_context(["defs1", "defs2"]))
    assert asset_graph.get_implicit_job_name_for_assets([asset1.key]) == "__ASSET_JOB"
    assert asset_graph.get_implicit_job_name_for_assets([asset2.key]) == "__ASSET_JOB"
    assert asset_graph.get_implicit_job_name_for_assets([asset1.key, asset2.key]) == "__ASSET_JOB"

    asset_graph = ExternalAssetGraph.from_workspace(make_context(["partitioned_defs"]))
    assert (
        asset_graph.get_implicit_job_name_for_assets([downstream_of_partitioned_source.key])
        == "__ASSET_JOB_0"
    )

    asset_graph = ExternalAssetGraph.from_workspace(make_context(["different_partitions_defs"]))
    assert (
        asset_graph.get_implicit_job_name_for_assets([static_partitioned_asset.key])
        == "__ASSET_JOB_0"
    )
    assert (
        asset_graph.get_implicit_job_name_for_assets([other_static_partitioned_asset.key])
        == "__ASSET_JOB_0"
    )
    assert (
        asset_graph.get_implicit_job_name_for_assets(
            [static_partitioned_asset.key, other_static_partitioned_asset.key]
        )
        == "__ASSET_JOB_0"
    )

    assert (
        asset_graph.get_implicit_job_name_for_assets([downstream_of_partitioned_source.key])
        == "__ASSET_JOB_1"
    )

    assert (
        asset_graph.get_implicit_job_name_for_assets(
            [
                static_partitioned_asset.key,
                other_static_partitioned_asset.key,
                downstream_of_partitioned_source.key,
            ]
        )
        is None
    )


def test_auto_materialize_policy():
    asset_graph = ExternalAssetGraph.from_workspace(make_context(["partitioned_defs"]))

    assert asset_graph.get_auto_materialize_policy(
        AssetKey("downstream_of_partitioned_source")
    ) == AutoMaterializePolicy(
        on_missing=True,
        for_freshness=True,
        on_new_parent_data=True,
        time_window_partition_scope_minutes=(24 + 7) * 60,
    )


@asset(
    ins={
        "static_partitioned_asset": AssetIn(
            partition_mapping=StaticPartitionMapping({"foo": "1", "bar": "2"})
        )
    },
    partitions_def=StaticPartitionsDefinition(["1", "2"]),
)
def partition_mapping_asset(static_partitioned_asset):
    pass


partition_mapping_defs = Definitions(assets=[static_partitioned_asset, partition_mapping_asset])


def test_partition_mapping():
    asset_graph = ExternalAssetGraph.from_workspace(make_context(["partition_mapping_defs"]))
    assert isinstance(
        asset_graph.get_partition_mapping(
            AssetKey("partition_mapping_asset"), AssetKey("static_partitioned_asset")
        ),
        StaticPartitionMapping,
    )
    assert isinstance(
        asset_graph.get_partition_mapping(
            AssetKey("static_partitioned_asset"), AssetKey("partition_mapping_asset")
        ),
        IdentityPartitionMapping,
    )
