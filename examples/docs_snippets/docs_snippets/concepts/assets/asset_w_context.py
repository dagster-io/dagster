from dagster import asset

# start_w_context


@asset(required_resource_keys={"alerter"})
def my_asset(context):
    # creates an asset and sends an alert to notify of its creation
    context.resources.alerter.send_asset_create_alert("my_asset")
    return [1, 2, 3]


# end_w_context
