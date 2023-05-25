from typing import List

from dagster import Config, In, Nothing, Out, Output, op
from pydantic import Field

from .resources import DEFAULT_POLL_INTERVAL, CensusResource
from .types import CensusOutput
from .utils import generate_materialization


class CensusTriggerSyncOpConfig(Config):
    sync_id: int = Field(description="ID of the parent sync.")
    force_full_sync: bool = Field(
        default=False,
        description=(
            "If this trigger request should be a Full Sync. "
            "Note that some sync configurations such as Append do not support full syncs."
        ),
    )
    poll_interval: float = Field(
        default=DEFAULT_POLL_INTERVAL,
        description="The time (in seconds) to wait between successive polls.",
    )
    poll_timeout: float = Field(
        default=None,
        description=(
            "The maximum time to wait before this operation is timed out. By "
            "default, this will never time out."
        ),
    )
    yield_materializations: bool = Field(
        default=True,
        description=(
            "If True, materializations corresponding to the results of the Census sync will "
            "be yielded when the op executes."
        ),
    )
    asset_key_prefix: List[str] = Field(
        default=["census"],
        description=(
            "If provided and yield_materializations is True, these components will be used to "
            "prefix the generated asset keys."
        ),
    )


@op(
    ins={"start_after": In(Nothing)},
    out=Out(
        CensusOutput,
        description=(
            "Parsed json dictionary representing the details of the Census sync after "
            "the sync successfully completes."
        ),
    ),
    tags={"kind": "census"},
)
def census_trigger_sync_op(config: CensusTriggerSyncOpConfig, census: CensusResource):
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
    census_output = census.trigger_sync_and_poll(
        sync_id=config.sync_id,
        force_full_sync=config.force_full_sync,
        poll_interval=config.poll_interval,
        poll_timeout=config.poll_timeout,
    )
    if config.yield_materializations:
        yield generate_materialization(census_output, asset_key_prefix=config.asset_key_prefix)
    yield Output(census_output)
