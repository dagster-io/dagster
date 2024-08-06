from dagster import asset, Definitions
import pandas as pd
from sqlalchemy import create_engine


@asset
def read_csv():
    df = pd.read_csv("path/to/your/file.csv")
    return df


@asset
def transform_data(read_csv):
    # Example transformation: Convert column names to lowercase
    transformed_df = read_csv.rename(columns=str.lower)
    return transformed_df


@asset
def load_to_postgres(transform_data):
    engine = create_engine("postgresql+psycopg2://username:password@localhost:5432/yourdatabase")
    transform_data.to_sql("your_table_name", engine, if_exists="replace", index=False)


defs = Definitions(assets=[load_to_postgres, transform_data, read_csv])
