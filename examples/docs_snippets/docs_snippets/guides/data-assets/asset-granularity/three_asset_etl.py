import dagster as dg


def extract_from_source(): ...


def load_to_staging(data): ...


def transform_data(data): ...


# start_three_assets
@dg.asset
def orders_extract(context: dg.AssetExecutionContext):
    """First asset: extract only."""
    return extract_from_source()


@dg.asset
def orders_load(context: dg.AssetExecutionContext, orders_extract):
    """Second asset: load from extract output (dependency inferred)."""
    return load_to_staging(orders_extract)


@dg.asset
def orders_transform(context: dg.AssetExecutionContext, orders_load):
    """Third asset: transform from load output."""
    return transform_data(orders_load)


# end_three_assets
