import dagster as dg
from dagster_duckdb import DuckDBResource
from project_dbt.defs.assets.metrics import manhattan_stats


def test_manhattan_stats_returns_row_count(tmp_path):
    db_path = str(tmp_path / "test.duckdb")
    db = DuckDBResource(database=db_path)

    with db.get_connection() as conn:
        conn.execute("CREATE TABLE daily_metrics (id INTEGER, value DOUBLE)")
        conn.execute("INSERT INTO daily_metrics VALUES (1, 10.0), (2, 20.0), (3, 30.0)")

    result = manhattan_stats(db)
    assert isinstance(result, dg.MaterializeResult)
    assert result.metadata["table_count"].value == 3


def test_manhattan_stats_empty_table(tmp_path):
    db_path = str(tmp_path / "test.duckdb")
    db = DuckDBResource(database=db_path)

    with db.get_connection() as conn:
        conn.execute("CREATE TABLE daily_metrics (id INTEGER)")

    result = manhattan_stats(db)
    assert result.metadata["table_count"].value == 0
