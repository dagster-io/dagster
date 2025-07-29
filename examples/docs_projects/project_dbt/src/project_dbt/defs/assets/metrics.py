import dagster as dg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dagster_duckdb import DuckDBResource


@dg.asset(
    deps=[
        dg.AssetKey(["taxi_daily_metrics"]),
    ],
    kinds={"duckdb"},
)
def manhattan_stats(database: DuckDBResource):
    query = """
        select *
        from daily_metrics
    """

    with database.get_connection() as conn:
        df = conn.execute(query).fetch_df()

        df["date_of_business"] = pd.to_datetime(df["date_of_business"])

        # Convert dates to strings for better labeling on the x-axis
        labels = df["date_of_business"].dt.strftime("%Y-%m-%d")
        x = np.arange(len(labels))  # label locations
        # Create bar chart
        fig, ax = plt.subplots(figsize=(10, 6))

        # Labels and formatting
        ax.set_xlabel("Date of Business")
        ax.set_title("Trip Count and Total Amount by Date")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45)
        ax.legend()
        ax.grid(axis="y")

        plt.tight_layout()
        plt.show()
