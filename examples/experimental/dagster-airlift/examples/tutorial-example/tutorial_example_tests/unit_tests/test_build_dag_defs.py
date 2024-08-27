from pathlib import Path

from dagster import Definitions
from tutorial_example.dagster_defs.build_dag_defs import build_dag_defs


def example_root() -> Path:
    return Path(__file__).parent.parent.parent


def dummy_duck_db_path() -> Path:
    return Path(__file__).parent / "does_not_exist.duckdb"


def test_dag_defs_construction_and_node_defs() -> None:
    defs = build_dag_defs(
        dbt_project_path=example_root() / "tutorial_example" / "shared" / "dbt",
        # not invoked during construction of defs so dummy is ok
        duckdb_path=dummy_duck_db_path(),
    )
    assert isinstance(defs, Definitions)
    Definitions.validate_loadable(defs)

    load_raw_customers = defs.get_assets_def(["raw_data", "raw_customers"])
    assert load_raw_customers.node_def.name == "load_csv_to_duckdb_raw_customers"

    customers_csv = defs.get_assets_def(["customers_csv"])
    assert customers_csv.node_def.name == "export_duckdb_to_csv_customers"

    customers = defs.get_assets_def(["customers"])
    assert customers.node_def.name == "build_jaffle_shop"
