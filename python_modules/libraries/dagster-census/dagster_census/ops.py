from dagster import Array, Bool, Field, In, Noneable, Nothing, Out, Output, op

from .resources import DEFAULT_POLL_INTERVAL
from .types import CensusOutput
from .utils import generate_materialization


@op(
    required_resource_keys={"census"},
    ins={"start_after": In(Nothing)},
    out=Out(
        CensusOutput,
        description=(
            "Parsed json dictionary representing the details of the Census sync after "
            "the sync successfully completes."
        ),
    ),
    config_schema={
        "sync_id": Field(
            int,
            is_required=True,
            description="Id of the parent sync.",
        ),
        "force_full_sync": Field(
            config=Bool,
            default_value=False,
            description=(
                "If this trigger request should be a Full Sync. "
                "Note that some sync configurations such as Append do not support full syncs."
            ),
        ),
        "poll_interval": Field(
            float,
            default_value=DEFAULT_POLL_INTERVAL,
            description="The time (in seconds) to wait between successive polls.",
        ),
        "poll_timeout": Field(
            Noneable(float),
            default_value=None,
            description=(
                "The maximum time to wait before this operation is timed out. By "
                "default, this will never time out."
            ),
        ),
        "yield_materializations": Field(
            config=Bool,
            default_value=True,
            description=(
                "If True, materializations corresponding to the results of the Census sync will "
                "be yielded when the op executes."
            ),
        ),
        "asset_key_prefix": Field(
            config=Array(str),
            default_value=["census"],
            description=(
                "If provided and yield_materializations is True, these components will be used to "
                "prefix the generated asset keys."
            ),
        ),
    },
    tags={"kind": "census"},
)
def census_trigger_sync_op(context):
    """Executes a Census sync for a given ``sync_id`` and polls until that sync completes, raising
    an error if it is unsuccessful.

    It outputs a :py:class:`~dagster_census.CensusOutput` which contains the details of the Census
    sync after it successfully completes.

    It requires the use of the :py:class:`~dagster_census.census_resource`, which allows it to
    communicate with the Census API.

    **Examples:**

    .. code-block:: python

        from dagster import job
        from dagster_census import census_resource, census_sync_op

        my_census_resource = census_resource.configured(
            {
                "api_key": {"env": "CENSUS_API_KEY"},
            }
        )

        sync_foobar = census_sync_op.configured({"sync_id": "foobar"}, name="sync_foobar")

        @job(resource_defs={"census": my_census_resource})
        def my_simple_census_job():
            sync_foobar()

    """
    census_output = context.resources.census.trigger_sync_and_poll(
        sync_id=context.op_config["sync_id"],
        force_full_sync=context.op_config["force_full_sync"],
        poll_interval=context.op_config["poll_interval"],
        poll_timeout=context.op_config["poll_timeout"],
    )
    if context.op_config["yield_materializations"]:
        yield generate_materialization(
            census_output, asset_key_prefix=context.op_config["asset_key_prefix"]
        )
    yield Output(census_output)
