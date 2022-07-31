from dagster_airbyte import build_airbyte_assets

from ..utils.constants import AIRBYTE_CONNECTION_ID

airbyte_assets = build_airbyte_assets(
    connection_id=AIRBYTE_CONNECTION_ID,
    destination_tables=["orders", "users"],
    asset_key_prefix=["postgres_replica"],
)
