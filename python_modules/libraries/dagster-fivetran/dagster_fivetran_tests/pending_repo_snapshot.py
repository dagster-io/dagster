import os

from dagster._core.definitions.definitions_class import Definitions
from dagster_fivetran import FivetranWorkspace

from dagster_fivetran_tests.conftest import TEST_ACCOUNT_ID, TEST_API_KEY, TEST_API_SECRET

snapshot_path = os.getenv("FIVETRAN_SNAPSHOT_PATH")

workspace = FivetranWorkspace(
    account_id=TEST_ACCOUNT_ID,
    api_key=TEST_API_KEY,
    api_secret=TEST_API_SECRET,
    snapshot_path=snapshot_path,
)

workspace.get_or_fetch_workspace_data()

defs = Definitions(resources={"fivetran": workspace})
