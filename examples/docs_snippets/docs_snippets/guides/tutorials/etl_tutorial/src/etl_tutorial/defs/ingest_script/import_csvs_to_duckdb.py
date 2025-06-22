import duckdb


def import_url_to_duckdb(url: str, duckdb_path: str, table_name: str):
    conn = duckdb.connect(duckdb_path)

    # Use a more specific table name based on the URL to avoid conflicts
    # Extract table name from URL or use a hash
    conn.execute(
        f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM read_csv_auto(?)",
        [url],
    )

    row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    assert row_count is not None
    row_count = row_count[0]

    conn.close()

    print(f"Successfully imported {row_count} rows into {table_name} table")  # noqa: T201


if __name__ == "__main__":
    urls = [
        "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv",
        "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv",
        "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv",
    ]

    duckdb_path = "/tmp/jaffle_platform.duckdb"
    for url in urls:
        table_name = url.split("/")[-1].split(".")[0]
        import_url_to_duckdb(url, duckdb_path, table_name)
