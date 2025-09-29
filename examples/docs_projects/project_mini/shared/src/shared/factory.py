import dagster as dg


def asset_factory(asset_name: str):
    @dg.asset(name=asset_name)
    def asset():
        return asset_name

    return asset
