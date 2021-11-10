from typing import Any, Dict

from dagster import Field, In, Noneable, Nothing, Out, op
from dagster_fivetran.resources import DEFAULT_POLL_INTERVAL


@op(
    ins={"start_after": In(Nothing)},
    out=Out(
        dict,
        description="Parsed json dictionary representing the details of the Fivetran connector after "
        "the sync successfully completes. "
        "See the [Fivetran API Docs](https://fivetran.com/docs/rest-api/connectors#retrieveconnectordetails) "
        "to see detailed information on this response.",
    ),
    config_schema={
        "connector_id": Field(
            str,
            is_required=True,
            description="The Fivetran Connector ID that this op will sync. You can retrieve this "
            'value from the "Setup" tab of a given connector in the Fivetran UI.',
        ),
        "poll_interval": Field(
            float,
            default_value=DEFAULT_POLL_INTERVAL,
            description="The time (in seconds) that will be waited between successive polls.",
        ),
        "poll_timeout": Field(
            Noneable(float),
            default_value=None,
            description="The maximum time that will waited before this operation is timed out. By "
            "default, this will never time out.",
        ),
    },
    required_resource_keys={"fivetran"},
)
def fivetran_sync_op(context) -> Dict[str, Any]:
    """
    This op executes a Fivetran sync for a given ``connector_id``, and polls until that sync
    completes, raising an error if it is unsuccessful. It outputs a dictionary which represents the
    details of the Fivetran connector after the sync successfully completes.

    It requires the use of the :py:class:`~dagster_fivetran.fivetran_resource`, which allows it to
    communicate with the Fivetran API.

    Examples:

    .. code-block:: python

        from dagster import job
        from dagster_fivetran import fivetran_resource, fivetran_sync_op

        my_fivetran_resource = fivetran_resource.configured(
            {
                "api_key": {"env": "FIVETRAN_API_KEY"},
                "api_secret": {"env": "FIVETRAN_API_SECRET"},
            }
        )

        sync_foobar = fivetran_sync_op.configured({"connector_id": "foobar"}, name="sync_foobar")

        @job(resource_defs={"fivetran": my_fivetran_resource})
        def my_simple_fivetran_job():
            sync_foobar()

        @job(resource_defs={"fivetran": my_fivetran_resource})
        def my_composed_fivetran_job():
            final_foobar_state = sync_foobar(start_after=some_op())
            other_op(final_foobar_state)
    """
    return context.resources.fivetran.sync_and_poll(
        connector_id=context.op_config["connector_id"],
        poll_interval=context.op_config["poll_interval"],
        poll_timeout=context.op_config["poll_timeout"],
    )
