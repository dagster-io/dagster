import os

from dagster._core.definitions.definitions_class import Definitions
from dagster_fivetran import FivetranWorkspace, load_fivetran_asset_specs

from dagster_fivetran_tests.conftest import TEST_ACCOUNT_ID, TEST_API_KEY, TEST_API_SECRET

snapshot_path = os.getenv("FIVETRAN_SNAPSHOT_PATH")

workspace = FivetranWorkspace(
    account_id=TEST_ACCOUNT_ID,
    api_key=TEST_API_KEY,
    api_secret=TEST_API_SECRET,
    snapshot_path=snapshot_path,
)

workspace.get_or_fetch_workspace_data()
fivetran_specs = load_fivetran_asset_specs(workspace=workspace)

defs = Definitions(assets=fivetran_specs)
