from typing import List

from dagster import EventLogEntry


class AssetLogsEventsSubscribe:
    def __init__(self, instance, asset_keys):
        self.instance = instance
        self.asset_keys = asset_keys
        self.observer = None

    def __call__(self, observer):
        self.observer = observer
        self.instance.event_log_storage.watch_asset_events(self.handle_new_events)
        return self

    def dispose(self):
        self.instance.event_log_storage.end_watch_asset_events(self.handle_new_events)
        if self.observer and callable(getattr(self.observer, "dispose", None)):
            self.observer.dispose()
        self.observer = None

    def handle_new_events(self, new_events: List[EventLogEntry]):
        filtered = list()

        for event in new_events:
            d_event = event.dagster_event
            if not d_event or not d_event.asset_key:
                continue
            if d_event.asset_key in self.asset_keys:
                filtered.append(event)

        if filtered:
            self.observer.on_next(filtered)
