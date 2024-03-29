from dagster import Definitions, asset


@asset(metadata={"foo": "buz"})
def upstream():
    return 1


@asset(metadata={"bar": "qux"})
def downstream(upstream):
    return upstream + 1


defs = Definitions(assets=[upstream, downstream])
