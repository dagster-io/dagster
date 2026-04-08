import duckdb
from etl_tutorial.defs.assets import serialize_duckdb_query


def _count(db_path: str, table: str) -> int:
    conn = duckdb.connect(db_path)
    result = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    conn.close()
    return result


def test_serialize_duckdb_query_creates_table(tmp_path):
    db_path = str(tmp_path / "test.duckdb")
    serialize_duckdb_query(db_path, "CREATE TABLE widgets (id INTEGER, name VARCHAR)")
    serialize_duckdb_query(db_path, "INSERT INTO widgets VALUES (1, 'foo'), (2, 'bar')")
    assert _count(db_path, "widgets") == 2


def test_serialize_duckdb_query_is_idempotent(tmp_path):
    db_path = str(tmp_path / "test.duckdb")
    serialize_duckdb_query(db_path, "CREATE OR REPLACE TABLE counters (n INTEGER)")
    serialize_duckdb_query(db_path, "INSERT INTO counters VALUES (10)")
    serialize_duckdb_query(db_path, "INSERT INTO counters VALUES (20)")
    conn = duckdb.connect(db_path)
    total = conn.execute("SELECT sum(n) FROM counters").fetchone()[0]
    conn.close()
    assert total == 30
