import pandas as pd
from pathlib import Path


if __name__ == "__main__":
    # Load the parquet file from disk
    information_schema_dir = Path('sdftarget/3f8198d/sdftarget/dbg/data/system/information_schema::sdf/tables')
    df_list = [pd.read_parquet(f, engine='pyarrow') for f in information_schema_dir.glob('*.parquet')]
    df = pd.concat(df_list, ignore_index=True)
    print(df)