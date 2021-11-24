import pytest

from consumption_datamart.assets.acme_lake.invoice_line_items import invoice_order_lines
from dagster.core.asset_defs import build_assets_job


@pytest.fixture(scope="class")
def invoice_order_asset_materialization():
    lake_assets_job = build_assets_job(
        name="test_lake_assets_job",
        assets=[
            invoice_order_lines
        ]
    )

    results = lake_assets_job.execute_in_process()
    assert results.success

    # TODO compute the asset materialization step number
    ASSET_MATERIALIZATION_STEP = 2
    return results.events_for_node('invoice_order_lines')[ASSET_MATERIALIZATION_STEP].step_materialization_data.materialization


@pytest.mark.usefixtures("invoice_order_asset_materialization")
class Test_invoice_line_items:

    def test_it_should_be_defined_as_a_dagster_asset(self, invoice_order_asset_materialization):
        assert invoice_order_asset_materialization.asset_key.path[0] == "acme_lake"
        assert invoice_order_asset_materialization.asset_key.path[1] == "invoice_order_lines"
