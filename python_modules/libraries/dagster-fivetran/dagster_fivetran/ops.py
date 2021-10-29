from typing import Dict, Any
from dagster import op, Field, In, Nothing, Noneable
from dagster_fivetran.resources import DEFAULT_POLL_INTERVAL


@op(
    ins={"start_after": In(Nothing)},
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
    return context.resources.fivetran.sync_and_poll(
        connector_id=context.op_config["connector_id"],
        poll_interval=context.op_config["poll_interval"],
        poll_timeout=context.op_config["poll_timeout"],
    )
