import dagster as dg


def _make_defs():
    @dg.asset
    def an_asset():
        pass

    return dg.Definitions(assets=[an_asset])


defs = _make_defs()
