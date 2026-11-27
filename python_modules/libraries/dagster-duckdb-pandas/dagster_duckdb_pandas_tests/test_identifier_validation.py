from pathlib import Path

import pandas as pd
import pytest
from dagster import DagsterInvariantViolationError, asset, materialize
from dagster_duckdb_pandas import DuckDBPandasIOManager


@asset(key_prefix=["my_schema"])
def my_table() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2, 3]})


@pytest.mark.parametrize("schema", ["s; drop table x", "s --", "s'", 's"', "my schema", "s()"])
def test_run_config_cannot_override_schema_with_unsafe_name(tmp_path: Path, schema: str) -> None:
    database = tmp_path / "unit_test.duckdb"
    io_manager = DuckDBPandasIOManager(database=str(database), schema="my_schema")

    with pytest.raises(DagsterInvariantViolationError, match="schema"):
        materialize(
            [my_table],
            resources={"io_manager": io_manager},
            run_config={
                "resources": {
                    "io_manager": {"config": {"database": str(database), "schema": schema}}
                }
            },
        )

    assert not database.exists()
