import os
import sys
import time
from unittest import mock

from dagster import Definitions, asset
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


def test_get_repository_location():
    def make_location_entry(attr: str):
        origin = InProcessRepositoryLocationOrigin(
            loadable_target_origin=LoadableTargetOrigin(
                executable_path=sys.executable,
                python_file=__file__,
                working_directory=os.path.dirname(__file__),
                attribute=attr,
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

    context = WorkspaceRequestContext(
        instance=mock.MagicMock(),
        workspace_snapshot={
            "loc1": make_location_entry("defs1"),
            "loc2": make_location_entry("defs2"),
        },
        process_context=mock.MagicMock(),
        version=None,
        source=None,
        read_only=True,
    )

    asset_graph = ExternalAssetGraph.from_workspace_request_context(context)

    assert asset_graph.get_job_names(asset1.key) == ["__ASSET_JOB"]
    repo_handle1 = asset_graph.get_repository_handle(asset1.key)
    assert repo_handle1.repository_name == "__repository__"
    assert repo_handle1.repository_python_origin.code_pointer.fn_name == "defs1"

    assert asset_graph.get_job_names(asset1.key) == ["__ASSET_JOB"]
    repo_handle2 = asset_graph.get_repository_handle(asset2.key)
    assert repo_handle2.repository_name == "__repository__"
    assert repo_handle2.repository_python_origin.code_pointer.fn_name == "defs2"
