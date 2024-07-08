from dagster import Definitions, asset


@asset
def upstream():
    return 1


defs = Definitions(assets=[upstream])
