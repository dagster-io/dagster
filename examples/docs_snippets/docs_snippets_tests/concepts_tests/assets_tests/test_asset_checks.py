import pytest
from mock import MagicMock

from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.events import AssetKey
from docs_snippets.concepts.assets.asset_checks.asset_with_check import (
    defs as asset_with_check_defs,
)
from docs_snippets.concepts.assets.asset_checks.factory import (
    check_blobs,
    defs as factory_defs,
    make_check,
)
from docs_snippets.concepts.assets.asset_checks.metadata import defs as metadata_defs
from docs_snippets.concepts.assets.asset_checks.orders_check import defs as orders_defs
from docs_snippets.concepts.assets.asset_checks.severity import defs as severity_defs


@pytest.mark.parametrize(
    "defs",
    [orders_defs, asset_with_check_defs, severity_defs, metadata_defs],
)
def test_execute(defs):
    job_def = defs.get_implicit_global_asset_job_def()
    result = job_def.execute_in_process()
    assert result.success


def test_factory():
    checks = [make_check(check_blob) for check_blob in check_blobs]
    assert [next(iter(c.check_keys)) for c in checks] == [
        AssetCheckKey(
            AssetKey(["orders"]),
            "orders_id_has_no_nulls",
        ),
        AssetCheckKey(
            AssetKey(["items"]),
            "items_id_has_no_nulls",
        ),
    ]


def test_factory_execute():
    job_def = factory_defs.get_implicit_global_asset_job_def()
    m = MagicMock()
    result = job_def.execute_in_process(resources={"db_connection": m})
    assert result.success
    assert m.execute.call_count == 2
    assert (
        m.execute.call_args_list[0][0][0] == "select * from items where item_id is null"
    )
    assert (
        m.execute.call_args_list[1][0][0]
        == "select * from orders where order_id is null"
    )
