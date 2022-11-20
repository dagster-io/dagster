from dagster import Definitions, asset


def dagster_defs():
    @asset
    def an_asset():
        pass

    return Definitions(assets=[an_asset])


# defs = dagster_defs()
