from dagster import asset

# start_w_context


@asset(required_resource_keys={"api"})
def my_asset(context):
    # fetches contents of an asset
    return context.resources.api.fetch_table("my_asset")


# end_w_context
