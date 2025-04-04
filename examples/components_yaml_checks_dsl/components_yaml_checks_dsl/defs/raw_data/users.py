import dagster as dg
import pandas as pd


@dg.asset(key=dg.AssetKey.from_user_string("RAW_DATA/users"))
def users(context: dg.AssetExecutionContext) -> pd.DataFrame:
    return pd.DataFrame()
