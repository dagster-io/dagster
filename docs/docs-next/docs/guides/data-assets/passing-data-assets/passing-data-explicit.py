import sqlite3
import tempfile

from dagster import AssetExecutionContext, Definitions, asset

database_file = tempfile.NamedTemporaryFile()


# highlight-start
@asset
def asset1():
    with sqlite3.connect("database.sqlite") as conn:
        conn.execute("CREATE OR REPLACE TABLE test (i INTEGER)")
        conn.execute("INSERT INTO test VALUES (42)")


@asset(deps=[asset1])
def asset2(context: AssetExecutionContext):
    with sqlite3.connect("database.sqlite") as conn:
        result = conn.execute("SELECT * FROM test").fetchall()
        context.log.info(result)
        # highlight-end


defs = Definitions(assets=[asset1, asset2])

if __name__ == "__main__":
    from dagster import materialize

    materialize(assets=[asset1, asset2])
