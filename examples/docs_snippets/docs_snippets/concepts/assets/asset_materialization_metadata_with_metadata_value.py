def generate_sales_dashboard():
    pass


# start

from dagster import AssetExecutionContext, MetadataValue, asset


@asset
def sales_dashboard(context: AssetExecutionContext):
    generate_sales_dashboard()
    context.add_output_metadata(
        metadata={"link": MetadataValue.url("http://mycoolsite.com/my_dashboard")}
    )


# end
