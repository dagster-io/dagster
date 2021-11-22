import json
from datetime import datetime

from dagster.core.telemetry import log_action


def log_dagit_telemetry_event(graphene_info, action, client_time, metadata):
    from ..schema.roots.mutation import GrapheneLogTelemetrySuccess

    instance = graphene_info.context.instance
    metadata = json.loads(metadata)
    client_time = datetime.utcfromtimestamp(int(client_time) / 1000)
    log_action(
        instance=instance,
        action=action,
        client_time=client_time,
        elapsed_time=None,
        metadata=metadata,
    )
    return GrapheneLogTelemetrySuccess(action=action)
