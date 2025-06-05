from dagster_sling import SlingResource, sling_assets

replication_config = {
    "source": "LOCAL",
    "target": "MY_DUCKDB",
    "defaults": {
        "mode": "full-refresh",
        "object": "{stream_table}",
    },
    "streams": {
        "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv": {"object": "main.raw_customers"},
        "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv": {"object": "main.raw_orders"},
        "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv": {"object": "main.raw_payments"},
    },
}

# TODO: Add this back in when we have a way to test it
# @sling_assets(
#     replication_config=replication_config,
# )
# def my_sling_assets(context, sling: SlingResource):
#     yield from sling.replicate(context=context)