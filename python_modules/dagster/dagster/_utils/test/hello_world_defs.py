from dagster import Definitions, asset


@asset
def hello_asset():
    pass


defs = Definitions(assets=[hello_asset])


# get_workspace_from_kwargs
