import contextvars

# Context variable to hold the current asset group name
_current_asset_group = contextvars.ContextVar("current_asset_group", default=None)

class asset_group:
    def __init__(self, group_name):
        self.group_name = group_name
        self.token = None

    def __enter__(self):
        self.token = _current_asset_group.set(self.group_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _current_asset_group.reset(self.token)

def get_current_asset_group():
    return _current_asset_group.get()
