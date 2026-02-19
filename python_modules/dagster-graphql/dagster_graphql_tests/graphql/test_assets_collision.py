
import pytest
from dagster import AssetKey, asset, repository, file_relative_path
from dagster._core.test_utils import instance_for_test
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import PythonFileTarget
from dagster_graphql.test.utils import execute_dagster_graphql

ASSET_DEFINITION_COLLISION_QUERY = """
    query AssetDefinitionCollisionQuery($assetKeys: [AssetKeyInput!]!) {
        assetNodeDefinitionCollisions(assetKeys: $assetKeys) {
            assetKey {
                path
            }
            repositories {
                id
                name
                location {
                    id
                    name
                }
            }
        }
    }
"""

ADDITIONAL_REQUIRED_KEYS_QUERY = """
    query AdditionalRequiredKeysQuery($assetKeys: [AssetKeyInput!]!) {
        assetNodeAdditionalRequiredKeys(assetKeys: $assetKeys) {
            path
        }
    }
"""

@asset
def asset_one():
    return 1

@repository
def repo_one():
    return [asset_one]

def test_collision_query_non_existent_asset():
    with instance_for_test() as instance:
        with WorkspaceProcessContext(
            instance,
            PythonFileTarget(
                python_file=file_relative_path(__file__, "test_assets_collision.py"),
                attribute="repo_one",
                working_directory=None,
                location_name="test_location",
            ),
        ) as workspace_process_context:
            context = workspace_process_context.create_request_context()
            
            # Test with a non-existent asset key
            # Before the fix, this would raise a KeyError
            result = execute_dagster_graphql(
                context,
                ASSET_DEFINITION_COLLISION_QUERY,
                variables={"assetKeys": [{"path": ["non_existent_asset"]}]},
            )
            
            assert result.data
            assert result.data["assetNodeDefinitionCollisions"] == []
            assert not result.errors

            # Test with an existing asset key
            result = execute_dagster_graphql(
                context,
                ASSET_DEFINITION_COLLISION_QUERY,
                variables={"assetKeys": [{"path": ["asset_one"]}]},
            )
            
            assert result.data
            assert result.data["assetNodeDefinitionCollisions"] == []
            assert not result.errors

def test_additional_required_keys_non_existent_asset():
    with instance_for_test() as instance:
        with WorkspaceProcessContext(
            instance,
            PythonFileTarget(
                python_file=file_relative_path(__file__, "test_assets_collision.py"),
                attribute="repo_one",
                working_directory=None,
                location_name="test_location",
            ),
        ) as workspace_process_context:
            context = workspace_process_context.create_request_context()

            # Test with a non-existent asset key
            # Before the fix, this would raise a KeyError
            result = execute_dagster_graphql(
                context,
                ADDITIONAL_REQUIRED_KEYS_QUERY,
                variables={"assetKeys": [{"path": ["non_existent_asset"]}]},
            )
            
            assert result.data
            assert result.data["assetNodeAdditionalRequiredKeys"] == []
            assert not result.errors
