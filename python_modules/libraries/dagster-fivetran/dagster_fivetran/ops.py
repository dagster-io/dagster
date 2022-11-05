from dagster_fivetran.resources import DEFAULT_POLL_INTERVAL
from dagster_fivetran.types import FivetranOutput
from dagster_fivetran.utils import generate_materializations

from dagster import Array, AssetKey, Bool, Field, In, Noneable, Nothing, Out, Output, Permissive, op


@op(
    required_resource_keys={"fivetran"},
    ins={"start_after": In(Nothing)},
    out=Out(
        FivetranOutput,
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
        "yield_materializations": Field(
            config=Bool,
            default_value=True,
            description=(
                "If True, materializations corresponding to the results of the Fivetran sync will "
                "be yielded when the op executes."
            ),
        ),
        "asset_key_prefix": Field(
            config=Array(str),
            default_value=["fivetran"],
            description=(
                "If provided and yield_materializations is True, these components will be used to "
                "prefix the generated asset keys."
            ),
        ),
    },
    tags={"kind": "fivetran"},
)
def fivetran_sync_op(context):
    """
    Executes a Fivetran sync for a given ``connector_id``, and polls until that sync
    completes, raising an error if it is unsuccessful. It outputs a FivetranOutput which contains
    the details of the Fivetran connector after the sync successfully completes, as well as details
    about which tables the sync updates.

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

    fivetran_output = context.resources.fivetran.sync_and_poll(
        connector_id=context.op_config["connector_id"],
        poll_interval=context.op_config["poll_interval"],
        poll_timeout=context.op_config["poll_timeout"],
    )
    if context.op_config["yield_materializations"]:
        yield from generate_materializations(
            fivetran_output, asset_key_prefix=context.op_config["asset_key_prefix"]
        )
    yield Output(fivetran_output)


@op(
    required_resource_keys={"fivetran"},
    ins={"start_after": In(Nothing)},
    out=Out(
        FivetranOutput,
        description="Parsed json dictionary representing the details of the Fivetran connector after "
        "the resync successfully completes. "
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
        "resync_parameters": Field(
            Noneable(Permissive()),
            default_value=None,
            description="Optional resync parameters to send in the payload to the Fivetran API. You "
            "can find an example resync payload here: https://fivetran.com/docs/rest-api/connectors#request_7",
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
        "yield_materializations": Field(
            config=Bool,
            default_value=True,
            description=(
                "If True, materializations corresponding to the results of the Fivetran sync will "
                "be yielded when the op executes."
            ),
        ),
        "asset_key_prefix": Field(
            config=Array(str),
            default_value=["fivetran"],
            description=(
                "If provided and yield_materializations is True, these components will be used to "
                "prefix the generated asset keys."
            ),
        ),
    },
    tags={"kind": "fivetran"},
)
def fivetran_resync_op(context):
    """
    Executes a Fivetran historical resync for a given ``connector_id``, and polls until that resync
    completes, raising an error if it is unsuccessful. It outputs a FivetranOutput which contains
    the details of the Fivetran connector after the resync successfully completes, as well as details
    about which tables the resync updates.

    It requires the use of the :py:class:`~dagster_fivetran.fivetran_resource`, which allows it to
    communicate with the Fivetran API.

    Examples:

    .. code-block:: python

        from dagster import job
        from dagster_fivetran import fivetran_resource, fivetran_resync_op

        my_fivetran_resource = fivetran_resource.configured(
            {
                "api_key": {"env": "FIVETRAN_API_KEY"},
                "api_secret": {"env": "FIVETRAN_API_SECRET"},
            }
        )

        sync_foobar = fivetran_resync_op.configured(
            {
                "connector_id": "foobar",
                "resync_parameters": {
                    "schema_a": ["table_a", "table_b"],
                    "schema_b": ["table_c"]
                }
            },
            name="sync_foobar"
        )

        @job(resource_defs={"fivetran": my_fivetran_resource})
        def my_simple_fivetran_job():
            sync_foobar()

        @job(resource_defs={"fivetran": my_fivetran_resource})
        def my_composed_fivetran_job():
            final_foobar_state = sync_foobar(start_after=some_op())
            other_op(final_foobar_state)
    """

    fivetran_output = context.resources.fivetran.resync_and_poll(
        connector_id=context.op_config["connector_id"],
        resync_parameters=context.op_config["resync_parameters"],
        poll_interval=context.op_config["poll_interval"],
        poll_timeout=context.op_config["poll_timeout"],
    )
    if context.op_config["yield_materializations"]:
        asset_key_filter = (
            [
                AssetKey(context.op_config["asset_key_prefix"] + [schema, table])
                for schema, tables in context.op_config["resync_parameters"].items()
                for table in tables
            ]
            if context.op_config["resync_parameters"] is not None
            else None
        )
        for mat in generate_materializations(
            fivetran_output, asset_key_prefix=context.op_config["asset_key_prefix"]
        ):
            if asset_key_filter is None or mat.asset_key in asset_key_filter:
                yield mat

    yield Output(fivetran_output)
