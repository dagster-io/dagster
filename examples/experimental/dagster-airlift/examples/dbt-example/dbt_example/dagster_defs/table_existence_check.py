from pathlib import Path

import duckdb
from dagster import AssetCheckResult, AssetChecksDefinition, AssetKey, asset_check


def build_table_existence_check(
    *, target_key: AssetKey, duckdb_path: Path, table_name: str, schema: str
) -> AssetChecksDefinition:
    @asset_check(asset=target_key)
    def table_exists() -> AssetCheckResult:
        assert duckdb_path.exists(), f"Expected {duckdb_path} to exist"
        con = duckdb.connect(str(duckdb_path))

        # Use information schema to check if table exists
        result = con.execute(
            f"""
SELECT COUNT(*) > 0 AS table_exists
FROM information_schema.tables
WHERE table_schema = '{schema}' AND table_name = '{table_name}';
            """
        ).fetchone()
        if not result or result[0] != 1:
            return AssetCheckResult(passed=False, description=f"Table {table_name} does not exist")
        return AssetCheckResult(passed=True, description=f"Table {table_name} exists")

    return table_exists
