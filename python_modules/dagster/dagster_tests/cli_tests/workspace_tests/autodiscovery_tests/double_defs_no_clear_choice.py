from dagster import Definitions


def _make_defs():
    return Definitions()


defs_foo = _make_defs()
defs_bar = _make_defs()
