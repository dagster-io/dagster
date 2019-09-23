import time

from dagster_graphql.implementation.reloader import Reloader

from dagster import check


class DagitReloader(Reloader):
    def __init__(self, reload_trigger):
        self.reload_trigger = check.opt_str_param(reload_trigger, 'reload_trigger')

    def is_reload_supported(self):
        return self.reload_trigger != None

    def reload(self):
        if not self.is_reload_supported:
            return False
        with open(self.reload_trigger, "w") as f:
            f.write(str(time.time()))
        return True
