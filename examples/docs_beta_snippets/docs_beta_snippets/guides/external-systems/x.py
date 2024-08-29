import dagster as dg

# An asset that uses a DuckDb resource called iris_db
@dg.asset
def iris_dataset() -> None:
    1



defs = dg.Definitions(
    assets=[iris_dataset],
)
