from dagster import AssetKey, AssetSpec, Definitions, multi_asset

from tutorial_example.shared.load_csv_to_duckdb import LoadCsvToDuckDbArgs, load_csv_to_duckdb


def load_csv_to_duckdb_defs(args: LoadCsvToDuckDbArgs) -> Definitions:
    @multi_asset(
        name=f"load_csv_to_duckdb_{args.table_name}",
        specs=[AssetSpec(key=AssetKey([args.duckdb_schema, args.table_name]))],
    )
    def _multi_asset() -> None:
        load_csv_to_duckdb(args)

    return Definitions(assets=[_multi_asset])
