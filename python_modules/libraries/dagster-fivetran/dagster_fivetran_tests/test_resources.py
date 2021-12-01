import datetime

import pytest
import responses
from dagster import Failure, build_init_resource_context
from dagster_fivetran import FivetranOutput, fivetran_resource

from .utils import (
    DEFAULT_CONNECTOR_ID,
    get_sample_connector_response,
    get_sample_connector_schema_config,
    get_sample_sync_response,
    get_sample_update_response,
)


def test_get_connector_details():

    ft_resource = fivetran_resource(
        build_init_resource_context(
            config={
                "api_key": "some_key",
                "api_secret": "some_secret",
            }
        )
    )

    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.GET,
            f"{ft_resource.api_base_url}{DEFAULT_CONNECTOR_ID}",
            json=get_sample_connector_response(),
        )
        assert (
            ft_resource.get_connector_details(DEFAULT_CONNECTOR_ID)
            == get_sample_connector_response()["data"]
        )


@pytest.mark.parametrize("max_retries,n_flakes", [(0, 0), (1, 2), (5, 7), (7, 5), (4, 4)])
def test_get_connector_details_flake(max_retries, n_flakes):

    ft_resource = fivetran_resource(
        build_init_resource_context(
            config={
                "api_key": "some_key",
                "api_secret": "some_secret",
                "request_max_retries": max_retries,
                "request_retry_delay": 0,
            }
        )
    )

    def _mock_interaction():
        with responses.RequestsMock() as rsps:
            # first n requests fail
            for _ in range(n_flakes):
                rsps.add(
                    rsps.GET,
                    f"{ft_resource.api_base_url}{DEFAULT_CONNECTOR_ID}",
                    status=500,
                )
            rsps.add(
                rsps.GET,
                f"{ft_resource.api_base_url}{DEFAULT_CONNECTOR_ID}",
                json=get_sample_connector_response(),
            )
            return ft_resource.get_connector_details(DEFAULT_CONNECTOR_ID)

    if n_flakes > max_retries:
        with pytest.raises(Failure, match="Exceeded max number of retries."):
            _mock_interaction()
    else:
        assert _mock_interaction() == get_sample_connector_response()["data"]


@pytest.mark.parametrize(
    "data,expected",
    [
        (
            {"succeeded_at": "2021-01-01T01:00:00.0Z", "failed_at": None},
            (datetime.datetime(2021, 1, 1, 1, 0, tzinfo=datetime.timezone.utc), True, "scheduled"),
        ),
        (
            {"succeeded_at": None, "failed_at": "2021-01-01T01:00:00.0Z"},
            (
                datetime.datetime(2021, 1, 1, 1, 0, tzinfo=datetime.timezone.utc),
                False,
                "scheduled",
            ),
        ),
        (
            {
                "succeeded_at": "2021-01-01T01:00:00.0Z",
                "failed_at": None,
                "status": {"sync_state": "foo"},
            },
            (datetime.datetime(2021, 1, 1, 1, 0, tzinfo=datetime.timezone.utc), True, "foo"),
        ),
        (
            {"succeeded_at": "2021-01-01T02:00:00.00Z", "failed_at": "2021-01-01T01:00:00.0Z"},
            (datetime.datetime(2021, 1, 1, 2, 0, tzinfo=datetime.timezone.utc), True, "scheduled"),
        ),
        (
            {"succeeded_at": "2021-01-01T01:00:00.0Z", "failed_at": "2021-01-01T02:00:00.00Z"},
            (
                datetime.datetime(2021, 1, 1, 2, 0, tzinfo=datetime.timezone.utc),
                False,
                "scheduled",
            ),
        ),
    ],
)
def test_get_connector_sync_status(data, expected):

    ft_resource = fivetran_resource(
        build_init_resource_context(
            config={
                "api_key": "some_key",
                "api_secret": "some_secret",
            }
        )
    )

    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.GET,
            f"{ft_resource.api_base_url}{DEFAULT_CONNECTOR_ID}",
            json=get_sample_connector_response(data=data),
        )
        assert ft_resource.get_connector_sync_status(DEFAULT_CONNECTOR_ID) == expected


@pytest.mark.parametrize(
    "n_polls, succeed_at_end",
    [(0, True), (0, False), (4, True), (4, False), (30, True)],
)
def test_sync_and_poll(n_polls, succeed_at_end):

    ft_resource = fivetran_resource(
        build_init_resource_context(
            config={
                "api_key": "some_key",
                "api_secret": "some_secret",
            }
        )
    )
    api_prefix = f"{ft_resource.api_base_url}{DEFAULT_CONNECTOR_ID}"

    final_data = (
        {"succeeded_at": "2021-01-01T02:00:00.0Z"}
        if succeed_at_end
        else {"failed_at": "2021-01-01T02:00:00.0Z"}
    )

    def _mock_interaction():

        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                f"{ft_resource.api_base_url}{DEFAULT_CONNECTOR_ID}/schemas",
                json=get_sample_connector_schema_config(),
            )
            rsps.add(rsps.PATCH, api_prefix, json=get_sample_update_response())
            rsps.add(rsps.POST, f"{api_prefix}/force", json=get_sample_sync_response())
            # initial state
            rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response())
            # n polls before updating
            for _ in range(n_polls):
                rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response())
            # final state will be updated
            rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response(data=final_data))
            return ft_resource.sync_and_poll(DEFAULT_CONNECTOR_ID, poll_interval=0.1)

    if succeed_at_end:
        assert _mock_interaction() == FivetranOutput(
            connector_details=get_sample_connector_response(data=final_data)["data"],
            schema_config=get_sample_connector_schema_config()["data"],
        )
    else:
        with pytest.raises(Failure, match="failed!"):
            _mock_interaction()


def test_sync_and_poll_timeout():

    ft_resource = fivetran_resource(
        build_init_resource_context(
            config={
                "api_key": "some_key",
                "api_secret": "some_secret",
            }
        )
    )

    with pytest.raises(Failure, match="timed out"):
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                f"{ft_resource.api_base_url}{DEFAULT_CONNECTOR_ID}/schemas",
                json=get_sample_connector_schema_config(),
            )
            rsps.add(
                rsps.GET,
                f"{ft_resource.api_base_url}{DEFAULT_CONNECTOR_ID}",
                json=get_sample_connector_response(),
            )
            rsps.add(
                rsps.PATCH,
                f"{ft_resource.api_base_url}{DEFAULT_CONNECTOR_ID}",
                json=get_sample_update_response(),
            )
            rsps.add(
                rsps.POST,
                f"{ft_resource.api_base_url}{DEFAULT_CONNECTOR_ID}/force",
                json=get_sample_sync_response(),
            )
            ft_resource.sync_and_poll(DEFAULT_CONNECTOR_ID, poll_interval=1, poll_timeout=2)


@pytest.mark.parametrize(
    "data,match",
    [
        ({"paused": True}, "paused"),
        ({"status": {"setup_state": "foo"}}, "setup"),
    ],
)
def test_sync_and_poll_invalid(data, match):

    ft_resource = fivetran_resource(
        build_init_resource_context(
            config={
                "api_key": "some_key",
                "api_secret": "some_secret",
            }
        )
    )

    with pytest.raises(Failure, match=match):
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                f"{ft_resource.api_base_url}{DEFAULT_CONNECTOR_ID}/schemas",
                json=get_sample_connector_schema_config(),
            )
            rsps.add(
                rsps.GET,
                f"{ft_resource.api_base_url}{DEFAULT_CONNECTOR_ID}",
                json=get_sample_connector_response(data=data),
            )
            rsps.add(
                rsps.PATCH,
                f"{ft_resource.api_base_url}{DEFAULT_CONNECTOR_ID}",
                json=get_sample_update_response(),
            )
            rsps.add(
                rsps.POST,
                f"{ft_resource.api_base_url}{DEFAULT_CONNECTOR_ID}/force",
                json=get_sample_sync_response(),
            )
            ft_resource.sync_and_poll(DEFAULT_CONNECTOR_ID, poll_interval=0.1)
