import dagster as dg


# start_scenario_a
# In code location 2, declare a dependency on an asset from code location 1
# using its AssetKey. The upstream asset is not loaded as input — the
# dependency only establishes lineage in the asset graph.
@dg.asset(deps=[dg.AssetKey("daily_sales_data")])
def weekly_sales_report() -> None:
    pass


# end_scenario_a


# start_scenario_b
@dg.io_manager
def warehouse_io_manager():
    class WarehouseIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            # load data from storage
            return [1, 2, 3]

    return WarehouseIOManager()


# Declare the upstream asset from code location 1 as an AssetSpec.
# This tells Dagster to load it via warehouse_io_manager at runtime.
daily_sales_data = dg.AssetSpec(key="daily_sales_data").with_io_manager_key(
    "warehouse_io_manager"
)


@dg.asset
def enriched_sales_data(daily_sales_data: list) -> list:
    # daily_sales_data is loaded from storage via warehouse_io_manager
    return [x * 2 for x in daily_sales_data]


# Include the AssetSpec alongside your assets in Definitions
defs = dg.Definitions(
    assets=[daily_sales_data, enriched_sales_data],
    resources={"warehouse_io_manager": warehouse_io_manager},
)
# end_scenario_b
