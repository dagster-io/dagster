import zlib
from contextlib import ExitStack
from typing import cast
from uuid import uuid4

import dagster as dg
import pytest
import responses
import yaml
from dagster._core.remote_representation.code_location import CodeLocation
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._core.test_utils import instance_for_test
from dagster._core.workspace.load import location_origins_from_config
from dagster._serdes import serialize_value
from dagster._utils import file_relative_path


@pytest.fixture
def instance():
    with instance_for_test() as instance:
        yield instance


def location_one_snapshot() -> RepositorySnap:
    @dg.asset
    def location_one_asset():
        return "location_one_asset"

    return RepositorySnap.from_def(dg.Definitions(assets=[location_one_asset]).get_repository_def())


def location_two_snapshot() -> RepositorySnap:
    @dg.asset
    def location_two_asset():
        return "location_two_asset"

    return RepositorySnap.from_def(dg.Definitions(assets=[location_two_asset]).get_repository_def())


def add_fake_hosted_location(snap: RepositorySnap) -> str:
    uuid = str(uuid4())
    fake_url = f"https://aws.com/location_{uuid}.json.gz"
    file = zlib.compress(serialize_value(snap).encode("utf-8"))
    responses.add(method=responses.GET, url=fake_url, body=file, status=200)
    return fake_url


@responses.activate
def test_plus_workspace(instance):
    MOCK_URL = "https://dagster.cloud"
    MOCK_TOKEN = "abc123"

    responses.add(
        method=responses.POST,
        url=f"{MOCK_URL}/graphql",
        json={
            "data": {
                "workspace": {
                    "workspaceEntries": [
                        {"locationName": "location_one"},
                        {"locationName": "location_two"},
                    ]
                },
            },
        },
        status=200,
    )

    location_one_fake_url = add_fake_hosted_location(location_one_snapshot())
    location_two_fake_url = add_fake_hosted_location(location_two_snapshot())

    responses.add(
        method=responses.GET,
        url=f"{MOCK_URL}/gen_code_location_snapshot_url?location_name=location_one",
        json={
            "repositories": [
                {
                    "repository_name": "repository_one",
                    "presigned_url": location_one_fake_url,
                    "presigned_job_urls": {},
                }
            ]
        },
        status=200,
    )
    responses.add(
        method=responses.GET,
        url=f"{MOCK_URL}/gen_code_location_snapshot_url?location_name=location_two",
        json={
            "repositories": [
                {
                    "repository_name": "repository_two",
                    "presigned_url": location_two_fake_url,
                    "presigned_job_urls": {},
                }
            ]
        },
        status=200,
    )

    workspace_yaml = f"""
load_from:
    - plus:
        url: {MOCK_URL}
        deployment: test
        token: {MOCK_TOKEN}
            """

    origins = location_origins_from_config(
        yaml.safe_load(workspace_yaml),
        # fake out as if it were loaded by a yaml file in this directory
        file_relative_path(__file__, "not_a_real.yaml"),
    )

    with ExitStack() as stack:
        code_locations = {
            name: stack.enter_context(origin.create_location(instance))
            for name, origin in origins.items()
        }
        assert len(code_locations) == 2

        code_location_one = cast(CodeLocation, code_locations["location_one"])
        repo_one = code_location_one.get_repository("repository_one")
        assert repo_one.asset_graph.get_all_asset_keys() == {dg.AssetKey("location_one_asset")}
        asset_one_snap = repo_one.get_asset_node_snap(dg.AssetKey("location_one_asset"))
        assert asset_one_snap
        assert not asset_one_snap.is_executable

        code_location_two = cast(CodeLocation, code_locations["location_two"])
        repo_two = code_location_two.get_repository("repository_two")
        assert repo_two.asset_graph.get_all_asset_keys() == {dg.AssetKey("location_two_asset")}
        asset_two_snap = repo_two.get_asset_node_snap(dg.AssetKey("location_two_asset"))
        assert asset_two_snap
        assert not asset_two_snap.is_executable
