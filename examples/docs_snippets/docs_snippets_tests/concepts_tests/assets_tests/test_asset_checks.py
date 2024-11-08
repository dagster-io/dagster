from datetime import datetime
from importlib import resources
from unittest import mock
from unittest.mock import MagicMock

import pytest
from dagster_tests.cli_tests.command_tests.assets import fail_asset

from dagster import Definitions
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.events import AssetKey
from docs_snippets.concepts.assets.asset_checks.asset_with_check import (
    defs as asset_with_check_defs,
)
from docs_snippets.concepts.assets.asset_checks.blocking import defs as blocking_defs
from docs_snippets.concepts.assets.asset_checks.factory import (
    check_blobs,
    defs as factory_defs,
    make_check,
)
from docs_snippets.concepts.assets.asset_checks.materializable_freshness_complete import (
    defs as materializable_freshness_complete_defs,
)
from docs_snippets.concepts.assets.asset_checks.materializable_freshness_in_pieces import (
    defs as materializable_freshness_in_pieces_defs,
)
from docs_snippets.concepts.assets.asset_checks.metadata import defs as metadata_defs
from docs_snippets.concepts.assets.asset_checks.orders_check import defs as orders_defs
from docs_snippets.concepts.assets.asset_checks.severity import defs as severity_defs
from docs_snippets.concepts.assets.asset_checks.source_data_freshness_complete import (
    defs as source_data_freshness_complete_defs,
)
from docs_snippets.concepts.assets.asset_checks.source_data_freshness_in_pieces import (
    defs as source_data_freshness_in_pieces_defs,
)


@pytest.mark.parametrize(
    "defs",
    [
        orders_defs,
        asset_with_check_defs,
        severity_defs,
        metadata_defs,
        materializable_freshness_in_pieces_defs,
        materializable_freshness_complete_defs,
    ],
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


def test_blocking_execute():
    job_def = blocking_defs.get_implicit_global_asset_job_def()
    result = job_def.execute_in_process(raise_on_error=False)
    assert not result.success
    assert len(result.get_asset_materialization_events()) == 1


@pytest.fixture
def mock_fetch_last_updated_timestamps():
    with mock.patch(
        "docs_snippets.concepts.assets.asset_checks.source_data_freshness_in_pieces.fetch_last_updated_timestamps"
    ) as m:
        with mock.patch(
            "docs_snippets.concepts.assets.asset_checks.source_data_freshness_complete.fetch_last_updated_timestamps"
        ) as m_complete:
            m.return_value = {"charges": 0.0, "customers": 0.0}
            m_complete.return_value = {"charges": 0.0, "customers": 0.0}
            yield


def test_source_data_freshness(mock_fetch_last_updated_timestamps: None):
    job_def = source_data_freshness_in_pieces_defs.get_implicit_global_asset_job_def()
    result = job_def.execute_in_process(resources={"snowflake": MagicMock()})
    assert result.success
    job_def = source_data_freshness_complete_defs.get_implicit_global_asset_job_def()
    result = job_def.execute_in_process(resources={"snowflake": MagicMock()})
    assert result.success
