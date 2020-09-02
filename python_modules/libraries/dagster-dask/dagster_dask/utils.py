import dask.dataframe as dd


def sanitize_column_names(df: dd.DataFrame) -> dd.DataFrame:
    df.columns = map(str.lower, df.columns)
    
    return df
