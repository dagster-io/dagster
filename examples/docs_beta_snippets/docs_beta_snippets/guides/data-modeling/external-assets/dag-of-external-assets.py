import dagster as dg

# highlight-start
# Three external assets that depend on each other
raw_data = dg.AssetSpec("raw_data")
stg_data = dg.AssetSpec("stg_data", deps=[raw_data])
cleaned_data = dg.AssetSpec("cleaned_data", deps=[stg_data])
# highlight-end


# Native asset that depends on an external asset
@dg.asset(deps=[cleaned_data])
def derived_data(): ...


# Define the Definitions object
defs = dg.Definitions(assets=[raw_data, stg_data, cleaned_data, derived_data])
