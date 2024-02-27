from dagster import Definitions, asset


@asset
def upstream():
    return 1


@asset
def downstream():
    return 2


defs = Definitions(assets=[upstream, downstream])
