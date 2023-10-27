import json
from datetime import datetime
from typing import TYPE_CHECKING

from dagster._core.telemetry import log_action

if TYPE_CHECKING:
    from dagster_graphql.schema.util import ResolveInfo

    from ..schema.roots.mutation import GrapheneLogTelemetrySuccess


def log_ui_telemetry_event(
    graphene_info: "ResolveInfo", action: str, client_time: str, client_id, metadata: str
) -> "GrapheneLogTelemetrySuccess":
    from ..schema.roots.mutation import GrapheneLogTelemetrySuccess

    instance = graphene_info.context.instance
    metadata = json.loads(metadata)
    assert isinstance(metadata, dict)
    client_datetime = datetime.utcfromtimestamp(int(client_time) / 1000)
    log_action(
        instance=instance,
        action=action,
        client_time=client_datetime,
        elapsed_time=None,
        metadata={"client_id": client_id, **metadata},
    )
    return GrapheneLogTelemetrySuccess(action=action)
