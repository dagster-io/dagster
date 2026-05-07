import dagster as dg


# start_decorator
@dg.asset(is_virtual=True)
def my_virtual_asset(upstream_asset):
    return upstream_asset


# end_decorator


# start_spec
my_virtual_spec = dg.AssetSpec(
    "my_virtual_asset", deps=["upstream_asset"], is_virtual=True
)
# end_spec
