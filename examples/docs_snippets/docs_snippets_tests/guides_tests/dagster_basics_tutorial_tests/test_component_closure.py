import importlib.util
from pathlib import Path

import dagster as dg
import pytest

from dagster._core.instance_for_test import instance_for_test


@pytest.mark.integration
def test_tutorial_component_creates_distinct_assets(tmp_path: Path) -> None:
    # Load the tutorial component module directly from the examples path
    tutorial_path = Path(
        "examples/docs_snippets/docs_snippets/guides/tutorials/dagster_tutorial/src/"
        "dagster_tutorial/components/tutorial.py"
    ).resolve()

    spec = importlib.util.spec_from_file_location("dagster_tutorial_tutorial", str(tutorial_path))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]

    ETL = getattr(mod, "ETL")
    Tutorial = getattr(mod, "Tutorial")

    # Create distinct CSVs so each asset has unique row counts
    customers_csv = tmp_path / "customers.csv"
    orders_csv = tmp_path / "orders.csv"
    payments_csv = tmp_path / "payments.csv"

    customers_csv.write_text("id,name\n1,Alice\n2,Bob\n", encoding="utf-8")
    orders_csv.write_text("id,amount\n10,100\n", encoding="utf-8")
    payments_csv.write_text("id,method\n100,card\n101,cash\n102,card\n", encoding="utf-8")

    db_path = tmp_path / "test.duckdb"

    component = Tutorial(
        duckdb_database=str(db_path),
        etl_steps=[
            ETL(url_path=str(customers_csv), table="customers"),
            ETL(url_path=str(orders_csv), table="orders"),
            ETL(url_path=str(payments_csv), table="payments"),
        ],
    )

    defs = component.build_defs(None)  # type: ignore[arg-type]

    # Verify all three assets are present
    assert {k.to_user_string() for k in defs.resolve_all_asset_keys()} == {
        "customers",
        "orders",
        "payments",
    }

    # Materialize each asset independently to ensure configs aren't shared
    job = defs.get_implicit_global_asset_job_def()
    with instance_for_test() as instance:
        for name in ("customers", "orders", "payments"):
            result = job.execute_in_process(instance=instance, asset_selection=[dg.AssetKey(name)])
            assert result.success

    # Inspect table row counts to ensure each asset used its own CSV
    try:
        import duckdb
    except Exception:  # pragma: no cover - envs without duckdb
        pytest.skip("duckdb not available in test environment")

    con = duckdb.connect(str(db_path))
    try:
        count_customers = con.execute("select count(*) from customers").fetchone()[0]
        count_orders = con.execute("select count(*) from orders").fetchone()[0]
        count_payments = con.execute("select count(*) from payments").fetchone()[0]

        assert count_customers == 2
        assert count_orders == 1
        assert count_payments == 3
    finally:
        con.close()
