import responses
from dagster import job, op
from dagster_census import CensusOutput, census_resource, census_trigger_sync_op

from dagster_census_tests.utils import (
    get_destination_data,
    get_source_data,
    get_sync_data,
    get_sync_run_data,
    get_sync_trigger_data,
)


def test_census_trigger_sync_op():
    cen_resource = census_resource.configured({"api_key": "foo"})

    @op
    def foo_op():
        pass

    @job(
        resource_defs={"census": cen_resource},
        config={
            "ops": {
                "census_trigger_sync_op": {
                    "config": {
                        "sync_id": 52,
                        "poll_interval": 0,
                        "poll_timeout": 10,
                    }
                }
            }
        },
    )
    def census_sync_job():
        census_trigger_sync_op(start_after=foo_op())

    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.GET,
            "https://app.getcensus.com/api/v1/syncs/52",
            json=get_sync_data(),
        )
        rsps.add(
            rsps.GET,
            "https://app.getcensus.com/api/v1/sources/15",
            json=get_source_data(),
        )
        rsps.add(
            rsps.GET,
            "https://app.getcensus.com/api/v1/destinations/15",
            json=get_destination_data(),
        )
        rsps.add(
            rsps.POST,
            "https://app.getcensus.com/api/v1/syncs/52/trigger",
            json=get_sync_trigger_data(),
        )
        rsps.add(
            rsps.GET,
            "https://app.getcensus.com/api/v1/sync_runs/94",
            json=get_sync_run_data(),
        )

        result = census_sync_job.execute_in_process()
        assert result.output_for_node("census_trigger_sync_op") == CensusOutput(
            sync_run=get_sync_run_data()["data"],
            source=get_source_data()["data"],
            destination=get_destination_data()["data"],
        )
