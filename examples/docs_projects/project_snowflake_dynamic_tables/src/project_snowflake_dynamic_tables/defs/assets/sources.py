import dagster as dg

# start_source_specs
raw_orders = dg.AssetSpec(
    key="raw_orders",
    group_name="sources",
    description="Raw order records loaded by the nightly ETL pipeline.",
    metadata={
        "snowflake_table": "ECOMMERCE.RAW.RAW_ORDERS",
        "owner": "data-engineering-team",
    },
    kinds={"snowflake"},
)

raw_customers = dg.AssetSpec(
    key="raw_customers",
    group_name="sources",
    description="Raw customer records loaded by the nightly ETL pipeline.",
    metadata={
        "snowflake_table": "ECOMMERCE.RAW.RAW_CUSTOMERS",
        "owner": "data-engineering-team",
    },
    kinds={"snowflake"},
)


# end_source_specs


@dg.definitions
def source_defs() -> dg.Definitions:
    return dg.Definitions(assets=[raw_orders, raw_customers])
