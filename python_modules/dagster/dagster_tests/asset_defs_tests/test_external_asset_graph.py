import os
import sys
import time
from unittest import mock

from dagster import AssetKey, Definitions, SourceAsset, asset
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.host_representation import InProcessRepositoryLocationOrigin
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._core.workspace.workspace import WorkspaceLocationEntry, WorkspaceLocationLoadStatus


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


def make_location_entry(defs_attr: str):
    origin = InProcessRepositoryLocationOrigin(
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

    repo_location = origin.create_location()

    return WorkspaceLocationEntry(
        origin=origin,
        repository_location=repo_location,
        load_error=None,
        load_status=WorkspaceLocationLoadStatus.LOADED,
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
    asset_graph = ExternalAssetGraph.from_workspace_request_context(
        make_context(["defs1", "defs2"])
    )

    assert asset_graph.get_job_names(asset1.key) == ["__ASSET_JOB"]
    repo_handle1 = asset_graph.get_repository_handle(asset1.key)
    assert repo_handle1.repository_name == "__repository__"
    assert repo_handle1.repository_python_origin.code_pointer.fn_name == "defs1"

    assert asset_graph.get_job_names(asset1.key) == ["__ASSET_JOB"]
    repo_handle2 = asset_graph.get_repository_handle(asset2.key)
    assert repo_handle2.repository_name == "__repository__"
    assert repo_handle2.repository_python_origin.code_pointer.fn_name == "defs2"


def test_cross_repo_dep_with_source_asset():
    asset_graph = ExternalAssetGraph.from_workspace_request_context(
        make_context(["defs1", "downstream_defs"])
    )
    assert len(asset_graph.source_asset_keys) == 0
    assert asset_graph.get_parents(AssetKey("downstream")) == {AssetKey("asset1")}
    assert asset_graph.get_children(AssetKey("asset1")) == {AssetKey("downstream")}
    assert (
        asset_graph.get_repository_handle(
            AssetKey("asset1")
        ).repository_python_origin.code_pointer.fn_name
        == "defs1"
    )
    assert (
        asset_graph.get_repository_handle(
            AssetKey("downstream")
        ).repository_python_origin.code_pointer.fn_name
        == "downstream_defs"
    )


def test_cross_repo_dep_no_source_asset():
    asset_graph = ExternalAssetGraph.from_workspace_request_context(
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
    assert (
        asset_graph.get_repository_handle(
            AssetKey("downstream_non_arg_dep")
        ).repository_python_origin.code_pointer.fn_name
        == "downstream_defs_no_source"
    )
