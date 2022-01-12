from dagster import Field, In, Noneable, Nothing, Out, Output, op
from dagster_airbyte.resources import DEFAULT_POLL_INTERVAL_SECONDS
from dagster_airbyte.types import AirbyteOutput


@op(
    required_resource_keys={"airbyte"},
    ins={"start_after": In(Nothing)},
    out=Out(
        AirbyteOutput,
        description="Parsed json dictionary representing the details of the Airbyte connector after "
        "the sync successfully completes. "
        "See the [Airbyte API Docs](https://airbyte-public-api-docs.s3.us-east-2.amazonaws.com/rapidoc-api-docs.html#overview) "
        "to see detailed information on this response.",
    ),
    config_schema={
        "connection_id": Field(
            str,
            is_required=True,
            description="The Airbyte Connection ID that this op will sync. You can retrieve this "
            'value from the "Connections" tab of a given connector in the Airbyte UI.',
        ),
        "poll_interval": Field(
            float,
            default_value=DEFAULT_POLL_INTERVAL_SECONDS,
            description="The time (in seconds) that will be waited between successive polls.",
        ),
        "poll_timeout": Field(
            Noneable(float),
            default_value=None,
            description="The maximum time that will waited before this operation is timed out. By "
            "default, this will never time out.",
        ),
    },
    tags={"kind": "airbyte"},
)
def airbyte_sync_op(context):
    """
    completes, raising an error if it is unsuccessful. It outputs a AirbyteOutput which contains
    Executes a Airbyte sync for a given ``connector_id``, and polls until that sync
    the details of the Airbyte connector after the sync successfully completes, as well as details
    about which tables the sync updates.

    It requires the use of the :py:class:`~dagster_airbyte.airbyte_resource`, which allows it to
    communicate with the Airbyte API.

    Examples:

    .. code-block:: python

        from dagster import job
        from dagster_airbyte import airbyte_resource, airbyte_sync_op

        my_airbyte_resource = airbyte_resource.configured(
            {
                "host": {"env": "AIRBYTE_HOST"},
                "port": {"env": "AIRBYTE_PORT"},
            }
        )

        sync_foobar = airbyte_sync_op.configured({"connection_id": "foobar"}, name="sync_foobar")

        @job(resource_defs={"fivetran": my_airbyte_resource})
        def my_simple_airbyte_job():
            sync_foobar()

        @job(resource_defs={"airbyte": my_airbyte_resource})
        def my_composed_airbyte_job():
            final_foobar_state = sync_foobar(start_after=some_op())
            other_op(final_foobar_state)
    """

    airbyte_output = context.resources.airbyte.sync_and_poll(
        connection_id=context.op_config["connection_id"],
        poll_interval=context.op_config["poll_interval"],
        poll_timeout=context.op_config["poll_timeout"],
    )
    yield Output(airbyte_output)
