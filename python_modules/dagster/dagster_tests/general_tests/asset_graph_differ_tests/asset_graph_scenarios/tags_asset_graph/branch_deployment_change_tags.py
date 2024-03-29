from dagster import Definitions, asset


@asset(tags={"foo": "buz"})
def upstream():
    return 1


@asset(tags={"bar": "qux"})
def downstream(upstream):
    return upstream + 1


defs = Definitions(assets=[upstream, downstream])
