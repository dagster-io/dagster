import dagster as dg

# Define an external asset with the key "raw_transactions".
# This will appear in the Dagster asset catalog, but cannot
# be materialized by Dagster itself.
# highlight-next-line
raw_transactions = dg.AssetSpec("raw_transactions")


# This asset is materialized by Dagster and depends on the
# external asset.
@dg.asset(deps=[raw_transactions])
def cleaned_transactions(): ...


# Define the Definitions object
defs = dg.Definitions(assets=[raw_transactions, cleaned_transactions])
