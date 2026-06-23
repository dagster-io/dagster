import dagster as dg


def extract_from_source(): ...


def load_to_staging(data): ...


def transform_data(data): ...


# start_single_asset
@dg.asset
def customer_etl_single(context: dg.AssetExecutionContext):
    """One asset: extract, load, and transform in a single function."""
    data = extract_from_source()
    loaded = load_to_staging(data)
    transformed = transform_data(loaded)
    return transformed


# end_single_asset
