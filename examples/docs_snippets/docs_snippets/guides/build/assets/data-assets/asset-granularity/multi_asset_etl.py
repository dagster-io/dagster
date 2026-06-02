import dagster as dg


def extract_from_source(): ...


def load_to_staging(data): ...


def transform_data(data): ...


# start_multi_asset
@dg.multi_asset(
    outs={
        "raw": dg.AssetOut(key="inventory_raw"),
        "staged": dg.AssetOut(key="inventory_staged"),
        "final": dg.AssetOut(key="inventory_final"),
    },
    can_subset=False,  # All outputs produced together
)
def inventory_etl_multi_asset(context: dg.AssetExecutionContext):
    """One function produces three assets; data passed in memory."""
    raw_data = extract_from_source()
    staged_data = load_to_staging(raw_data)
    final_data = transform_data(staged_data)
    return raw_data, staged_data, final_data


# end_multi_asset
