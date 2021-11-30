import pytest

from consumption_datamart.assets.acme_lake.invoice_line_items import invoice_order_lines, InvoiceOrderItemsDataFrameType
from consumption_datamart.resources.datawarehouse_resources import inmemory_datawarehouse_resource
from dagster.core.asset_defs import build_assets_job


@pytest.fixture(scope="class")
def invoice_order_asset_job_results():
    lake_assets_job = build_assets_job(
        name="test_lake_assets_job",
        resource_defs={
            "datawarehouse": inmemory_datawarehouse_resource.configured({
                "log_sql": False
            })
        },
        assets=[
            invoice_order_lines
        ]
    )

    results = lake_assets_job.execute_in_process()
    assert results.success

    return results


@pytest.mark.usefixtures("invoice_order_asset_job_results")
class Test_invoice_line_items:

    @staticmethod
    def get_invoice_order_lines_materialization(invoice_order_asset_job_results):
        # TODO compute the asset materialization step number
        ASSET_MATERIALIZATION_STEP = 2
        asset_materialization = invoice_order_asset_job_results.events_for_node('invoice_order_lines')[
            ASSET_MATERIALIZATION_STEP].step_materialization_data.materialization
        return asset_materialization

    def test_it_should_be_defined_as_a_dagster_asset(self, invoice_order_asset_job_results):
        asset_materialization = self.get_invoice_order_lines_materialization(invoice_order_asset_job_results)

        assert asset_materialization.asset_key.path[0] == "acme_lake"
        assert asset_materialization.asset_key.path[1] == "invoice_order_lines"

    def test_it_should_pass_type_validation(self, invoice_order_asset_job_results):
        typed_df = invoice_order_asset_job_results.output_for_node('invoice_order_lines')
        type_check_result = InvoiceOrderItemsDataFrameType.type_check(context=None, value=typed_df)
        assert type_check_result.success, type_check_result.description

    def test_rows_with_missing_customer_information_should_have_warnings(self, invoice_order_asset_job_results):
        typed_df = invoice_order_asset_job_results.output_for_node('invoice_order_lines')

        assert typed_df[typed_df['invoice_id'] == 'INV-003-invalid-order'].meta__warnings.item() == 'invalid_customer_id;non_vcpu_sku'

    def test_asset_materialization_should_contain_a_warnings_count(self, invoice_order_asset_job_results):
        asset_materialization = self.get_invoice_order_lines_materialization(invoice_order_asset_job_results)

        assert asset_materialization.metadata_entries[2].entry_data.value == 2
