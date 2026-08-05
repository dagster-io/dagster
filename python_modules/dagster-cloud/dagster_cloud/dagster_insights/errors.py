class DagsterInsightsError(Exception):
    def __init__(self, *args, body=None):
        super().__init__(*args)
        self.body = body
