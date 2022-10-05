from typing import List
from dagster import EventLogEntry


class AssetLogsEventsSubscribe:
    def __init__(self, instance, asset_nodes):
        self.instance = instance
        self.asset_nodes = asset_nodes
        self.asset_match_set = set()
        for node in asset_nodes:
            self.asset_match_set.add(node.asset_key.to_string())
            for job_name in node.job_names:
                for op_name in node.op_names:
                    self.asset_match_set.add(f"{job_name}-{op_name}")

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
            step_hash = f"{d_event.pipeline_name}-{d_event.step_key}"
            asset_hash = d_event.asset_key.to_string() if d_event.asset_key else None
            if step_hash in self.asset_match_set or asset_hash in self.asset_match_set:
                filtered.append(event)

        if filtered:
            self.observer.on_next(filtered)
