import sqlite3

import dagster as dg


# highlight-start
@dg.asset
def asset1():
    with sqlite3.connect("database.sqlite") as conn:
        conn.execute("CREATE OR REPLACE TABLE test (i INTEGER)")
        conn.execute("INSERT INTO test VALUES (42)")


@dg.asset(deps=[asset1])
def asset2(context: dg.AssetExecutionContext):
    with sqlite3.connect("database.sqlite") as conn:
        result = conn.execute("SELECT * FROM test").fetchall()
        context.log.info(result)
        # highlight-end


defs = dg.Definitions(assets=[asset1, asset2])

if __name__ == "__main__":
    dg.materialize(assets=[asset1, asset2])
