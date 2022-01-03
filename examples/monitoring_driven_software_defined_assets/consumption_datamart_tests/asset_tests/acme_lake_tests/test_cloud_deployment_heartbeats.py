import pytest

from consumption_datamart.assets.acme_lake.cloud_deployment_heartbeats import cloud_deployment_heartbeats, CloudDeploymentHeartbeatsDataFrameType
from consumption_datamart.resources.datawarehouse_resources import inmemory_datawarehouse_resource
from dagster.core.asset_defs import build_assets_job
from consumption_datamart.resources.datawarehouse_io_manager import inmemory_datawarehouse_io_manager

@pytest.fixture(scope="class")
def cloud_deployment_heartbeats_job_results():
    lake_assets_job = build_assets_job(
        name="test_lake_assets_job",
        resource_defs={
            "datawarehouse": inmemory_datawarehouse_resource.configured({
                "log_sql": False
            }),
            "datawarehouse_io_manager": inmemory_datawarehouse_io_manager.configured({
                "log_sql": True
            }),
        },
        assets=[],
        source_assets=[
            cloud_deployment_heartbeats
        ]
    )

    results = lake_assets_job.execute_in_process()
    assert results.success

    return results


@pytest.mark.usefixtures("cloud_deployment_heartbeats_job_results")
@pytest.mark.skip(reason="Not sure how to trigger a ForeignAsset 'run'")
class Test_cloud_deployment_heartbeats:

    def test_it_should_be_defined_as_a_dagster_asset(self, cloud_deployment_heartbeats_job_results):
        # TODO compute the asset materialization step number
        ASSET_MATERIALIZATION_STEP = 2
        asset_materialization = cloud_deployment_heartbeats_job_results.events_for_node('cloud_deployment_heartbeats')[ASSET_MATERIALIZATION_STEP].step_materialization_data.materialization

        assert asset_materialization.asset_key.path[0] == "acme_lake"
        assert asset_materialization.asset_key.path[1] == "cloud_deployment_heartbeats"

    def test_it_should_pass_type_validation(self, cloud_deployment_heartbeats_job_results):
        typed_df = cloud_deployment_heartbeats_job_results.output_for_node('cloud_deployment_heartbeats')
        type_check_result = CloudDeploymentHeartbeatsDataFrameType.type_check(context=None, value=typed_df)
        assert type_check_result.success, type_check_result.description
