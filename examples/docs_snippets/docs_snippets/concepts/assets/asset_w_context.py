from dagster import asset

# start_w_context


@asset
def context_asset(context):
    context.log.info("My run ID is {context.run_id}")
    ...


# end_w_context
