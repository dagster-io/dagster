from dagster_dbt.cloud_v2.client import DbtCloudWorkspaceClient
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace


def test_dbt_cloud_client_connection(workspace: DbtCloudWorkspace) -> None:
    """Test that we can create a DbtCloudWorkspaceClient and verify its connection successfully."""
    client = workspace.get_client()
    assert isinstance(client, DbtCloudWorkspaceClient)

    client.verify_connection()
