class PipelineRunObservableSubscribe:
    def __init__(self, instance, run_id, after_cursor=None):
        self.instance = instance
        self.run_id = run_id
        self.observer = None
        self.after_cursor = after_cursor if after_cursor is not None else -1

    def __call__(self, observer):
        self.observer = observer

        events = self.instance.logs_after(self.run_id, self.after_cursor)
        if events:
            self.observer.on_next(events)

        cursor = len(events) + int(self.after_cursor)
        self.instance.watch_event_logs(self.run_id, cursor, self.handle_new_event)

    def handle_new_event(self, new_event):
        self.observer.on_next([new_event])
