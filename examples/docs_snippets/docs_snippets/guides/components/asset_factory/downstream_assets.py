import dagster as dg


@dg.asset(deps=[dg.AssetKey("etl_my_bucket_cleaned_transactions_csv")])
def downstream_cleaned_transactions_asset(context: dg.AssetExecutionContext): ...


@dg.asset(deps=[dg.AssetKey("etl_my_bucket_risky_customers_csv")])
def downstream_risky_customers_asset(context: dg.AssetExecutionContext): ...
