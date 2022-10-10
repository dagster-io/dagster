import graphene
from dagster_graphql.implementation.asset_subscription import AssetLogsEventsSubscribe
from dagster_graphql.implementation.events import from_dagster_event_record
from dagster_graphql.schema.logs.events import (
    GrapheneAssetMaterializationPlannedEvent,
    GrapheneMaterializationEvent,
    GrapheneObservationEvent,
)
from rx import Observable

from dagster._core.events.log import EventLogEntry

from .util import non_null_list


class GrapheneAssetLogEventsSubscriptionEvent(graphene.Union):
    class Meta:
        types = (
            GrapheneMaterializationEvent,
            GrapheneObservationEvent,
            GrapheneAssetMaterializationPlannedEvent,
        )
        name = "AssetLogEventsSubscriptionEvent"


class GrapheneAssetLogEventsSubscriptionSuccess(graphene.ObjectType):
    events = non_null_list(GrapheneAssetLogEventsSubscriptionEvent)

    class Meta:
        name = "AssetLogEventsSubscriptionSuccess"


class GrapheneAssetLogEventsSubscriptionFailure(graphene.ObjectType):
    message = graphene.NonNull(graphene.String)

    class Meta:
        name = "AssetLogEventsSubscriptionFailure"


class GrapheneAssetLogEventsSubscriptionPayload(graphene.Union):
    class Meta:
        types = (
            GrapheneAssetLogEventsSubscriptionSuccess,
            GrapheneAssetLogEventsSubscriptionFailure,
        )
        name = "AssetLogEventsSubscriptionPayload"


def get_asset_log_events_observable(graphene_info, asset_keys):
    instance = graphene_info.context.instance

    if not asset_keys:

        def _get_error_observable(observer):
            observer.on_next(
                GrapheneAssetLogEventsSubscriptionFailure(message="No asset nodes were specified")
            )

        return Observable.create(_get_error_observable)  # pylint: disable=E1101

    if not instance.event_log_storage.supports_watch_asset_events():

        def _get_error_observable(observer):
            observer.on_next(
                GrapheneAssetLogEventsSubscriptionFailure(
                    message="This feature is not supported by the event log storage engine"
                )
            )

        return Observable.create(_get_error_observable)  # pylint: disable=E1101

    def _handle_events(events: EventLogEntry):
        return GrapheneAssetLogEventsSubscriptionSuccess(
            events=[
                from_dagster_event_record(event, event.dagster_event.pipeline_name)
                for event in events
            ],
        )

    # pylint: disable=E1101
    return Observable.create(AssetLogsEventsSubscribe(instance, asset_keys)).map(_handle_events)


types = [
    GrapheneAssetLogEventsSubscriptionEvent,
    GrapheneAssetLogEventsSubscriptionSuccess,
    GrapheneAssetLogEventsSubscriptionFailure,
    GrapheneAssetLogEventsSubscriptionPayload,
]
