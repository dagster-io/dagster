from dagster import Definitions, asset


def build_defs():
    @asset
    def asset1(): ...

    return Definitions(assets=[asset1])
