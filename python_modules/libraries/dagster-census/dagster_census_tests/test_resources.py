import responses
from dagster_census import CensusOutput, CensusResource

from dagster_census_tests.utils import (
    get_destination_data,
    get_source_data,
    get_sync_data,
    get_sync_run_data,
    get_sync_trigger_data,
)


def test_get_sync():
    census = CensusResource(api_key="foo")
    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.GET,
            "https://app.getcensus.com/api/v1/syncs/52",
            json=get_sync_data(),
        )
        assert census.get_sync(sync_id="52")  # pyright: ignore[reportArgumentType]


def test_get_source():
    census = CensusResource(api_key="foo")
    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.GET,
            "https://app.getcensus.com/api/v1/sources/15",
            json=get_source_data(),
        )
        assert census.get_source(source_id="15")  # pyright: ignore[reportArgumentType]


def test_get_destination():
    census = CensusResource(api_key="foo")
    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.GET,
            "https://app.getcensus.com/api/v1/destinations/15",
            json=get_destination_data(),
        )
        assert census.get_destination(destination_id="15")  # pyright: ignore[reportArgumentType]


def test_get_sync_run():
    census = CensusResource(api_key="foo")
    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.GET,
            "https://app.getcensus.com/api/v1/sync_runs/94",
            json=get_sync_run_data(),
        )
        assert census.get_sync_run(sync_run_id="94")  # pyright: ignore[reportArgumentType]


def test_trigger_sync():
    census = CensusResource(api_key="foo")
    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.POST,
            "https://app.getcensus.com/api/v1/syncs/52/trigger",
            json=get_sync_trigger_data(),
        )
        assert census.trigger_sync(sync_id="52")  # pyright: ignore[reportArgumentType]


def test_trigger_sync_and_poll():
    census = CensusResource(api_key="foo")
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
        result = census.trigger_sync_and_poll(sync_id="52", poll_interval=0)  # pyright: ignore[reportArgumentType]
        assert result == CensusOutput(
            sync_run=get_sync_run_data()["data"],
            source=get_source_data()["data"],
            destination=get_destination_data()["data"],
        )


def test_resource_init():
    cen_resource = CensusResource(api_key="foo")

    assert type(cen_resource) is CensusResource
    assert cen_resource.api_base_url == "https://app.getcensus.com/api/v1"
