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
        return self

    def dispose(self):
        # called when the connection gets closed, allowing the observer to get GC'ed
        if self.observer and callable(getattr(self.observer, "dispose", None)):
            self.observer.dispose()
        self.observer = None
        self.instance.end_watch_event_logs(self.run_id, self.handle_new_event)

    def handle_new_event(self, new_event):
        if self.observer:
            self.observer.on_next([new_event])
