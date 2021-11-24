import pytest

from consumption_datamart.assets.acme_lake.cloud_deployment_heartbeats import cloud_deployment_heartbeats
from dagster.core.asset_defs import build_assets_job


@pytest.fixture(scope="class")
def cloud_deployment_heartbeats_materialization():
    lake_assets_job = build_assets_job(
        name="test_lake_assets_job",
        assets=[
            cloud_deployment_heartbeats
        ]
    )

    results = lake_assets_job.execute_in_process()
    assert results.success

    # TODO compute the asset materialization step number
    ASSET_MATERIALIZATION_STEP = 2
    return results.events_for_node('cloud_deployment_heartbeats')[ASSET_MATERIALIZATION_STEP].step_materialization_data.materialization


@pytest.mark.usefixtures("cloud_deployment_heartbeats_materialization")
class Test_cloud_deployment_heartbeats:

    def test_it_should_be_defined_as_a_dagster_asset(self, cloud_deployment_heartbeats_materialization):
        assert cloud_deployment_heartbeats_materialization.asset_key.path[0] == "acme_lake"
        assert cloud_deployment_heartbeats_materialization.asset_key.path[1] == "cloud_deployment_heartbeats"
