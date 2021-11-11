import responses
from dagster import job, op
from dagster_fivetran import fivetran_resource, fivetran_sync_op
from dagster_fivetran.resources import FIVETRAN_API_BASE, FIVETRAN_CONNECTOR_PATH

from .utils import (
    DEFAULT_CONNECTOR_ID,
    get_sample_connector_response,
    get_sample_sync_response,
    get_sample_update_response,
)


def test_fivetran_sync_op():

    ft_resource = fivetran_resource.configured({"api_key": "foo", "api_secret": "bar"})
    final_data = {"succeeded_at": "2021-01-01T02:00:00.0Z"}
    api_prefix = f"{FIVETRAN_API_BASE}/{FIVETRAN_CONNECTOR_PATH}{DEFAULT_CONNECTOR_ID}"

    @op
    def foo_op():
        pass

    @job(
        resource_defs={"fivetran": ft_resource},
        config={
            "ops": {
                "fivetran_sync_op": {
                    "config": {
                        "connector_id": DEFAULT_CONNECTOR_ID,
                        "poll_interval": 0.1,
                        "poll_timeout": 10,
                    }
                }
            }
        },
    )
    def fivetran_sync_job():
        fivetran_sync_op(start_after=foo_op())

    with responses.RequestsMock() as rsps:
        rsps.add(rsps.PATCH, api_prefix, json=get_sample_update_response())
        rsps.add(rsps.POST, f"{api_prefix}/force", json=get_sample_sync_response())
        # initial state
        rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response())
        # n polls before updating
        for _ in range(2):
            rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response())
        # final state will be updated
        rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response(data=final_data))

        result = fivetran_sync_job.execute_in_process()
        assert (
            result.output_for_node("fivetran_sync_op")
            == get_sample_connector_response(data=final_data)["data"]
        )
