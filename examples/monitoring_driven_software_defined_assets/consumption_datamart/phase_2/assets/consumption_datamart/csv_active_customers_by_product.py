from dagster import AssetKey
from dagster.core.asset_defs import ForeignAsset

csv_active_customers_by_product = ForeignAsset(
    key=AssetKey(['phase_2', 'acme_lake', 'csv_active_customers_by_product']),
    description="A manually curated list of active customers for a specific day",
    io_manager_key="fs_csv_io_manager",
)
