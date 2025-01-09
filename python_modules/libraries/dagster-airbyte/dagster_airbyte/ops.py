from collections.abc import Iterable
from typing import Any, Optional

from dagster import Config, In, Nothing, Out, Output, op
from dagster._core.storage.tags import COMPUTE_KIND_TAG
from pydantic import Field

from dagster_airbyte.resources import DEFAULT_POLL_INTERVAL_SECONDS, BaseAirbyteResource
from dagster_airbyte.types import AirbyteOutput
from dagster_airbyte.utils import _get_attempt, generate_materializations


class AirbyteSyncConfig(Config):
    connection_id: str = Field(
        ...,
        description=(
            "Parsed json dictionary representing the details of the Airbyte connector after the"
            " sync successfully completes. See the [Airbyte API"
            " Docs](https://airbyte-public-api-docs.s3.us-east-2.amazonaws.com/rapidoc-api-docs.html#overview)"
            " to see detailed information on this response."
        ),
    )
    poll_interval: float = Field(
        DEFAULT_POLL_INTERVAL_SECONDS,
        description=(
            "The maximum time that will waited before this operation is timed out. By "
            "default, this will never time out."
        ),
    )
    poll_timeout: Optional[float] = Field(
        None,
        description=(
            "The maximum time that will waited before this operation is timed out. By "
            "default, this will never time out."
        ),
    )
    yield_materializations: bool = Field(
        True,
        description=(
            "If True, materializations corresponding to the results of the Airbyte sync will "
            "be yielded when the op executes."
        ),
    )
    asset_key_prefix: list[str] = Field(
        ["airbyte"],
        description=(
            "If provided and yield_materializations is True, these components will be used to "
            "prefix the generated asset keys."
        ),
    )


@op(
    ins={"start_after": In(Nothing)},
    out=Out(
        AirbyteOutput,
        description=(
            "Parsed json dictionary representing the details of the Airbyte connector after the"
            " sync successfully completes. See the [Airbyte API"
            " Docs](https://airbyte-public-api-docs.s3.us-east-2.amazonaws.com/rapidoc-api-docs.html#overview)"
            " to see detailed information on this response."
        ),
    ),
    tags={COMPUTE_KIND_TAG: "airbyte"},
)
def airbyte_sync_op(
    context, config: AirbyteSyncConfig, airbyte: BaseAirbyteResource
) -> Iterable[Any]:
    """Executes a Airbyte job sync for a given ``connection_id``, and polls until that sync
    completes, raising an error if it is unsuccessful. It outputs a AirbyteOutput which contains
    the job details for a given ``connection_id``.

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

            @job(resource_defs={"airbyte": my_airbyte_resource})
            def my_simple_airbyte_job():
                sync_foobar()

            @job(resource_defs={"airbyte": my_airbyte_resource})
            def my_composed_airbyte_job():
                final_foobar_state = sync_foobar(start_after=some_op())
                other_op(final_foobar_state)
    """
    airbyte_output = airbyte.sync_and_poll(
        connection_id=config.connection_id,
        poll_interval=config.poll_interval,
        poll_timeout=config.poll_timeout,
    )
    if config.yield_materializations:
        yield from generate_materializations(
            airbyte_output, asset_key_prefix=config.asset_key_prefix
        )
    yield Output(
        airbyte_output,
        metadata={
            **_get_attempt(airbyte_output.job_details.get("attempts", [{}])[-1]).get(
                "totalStats", {}
            )
        },
    )
