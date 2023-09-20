from dagster import Config, op, In, Out, Nothing, Output

from typing import Any, Iterable, Generator, List

from .types import SlingOutput
from .resources import SlingResource, SlingSource, SlingTarget, SlingMode


class SlingSyncConfig(Config):
    source: SlingSource
    target: SlingTarget
    mode: SlingMode


@op(
    ins={"start_after": In(Nothing)},
    out=Out(
        List[str],
        description="TODO",
    ),
    tags={"kind": "sling"},
)
def sling_sync_op(context, config: SlingSyncConfig, sling: SlingResource) -> List[str]:
    """Runs a Sling sync operation."""
    context.log.info("Running Sling sync...")
    sling_output = sling.sync(source=config.source, target=config.target, mode=config.mode)
    stdout = [msg for msg in sling_output]
    yield Output(stdout)
