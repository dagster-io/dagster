from dagster import Definitions, asset


@asset(metadata={"foo": "bar"})
def upstream():
    return 1


@asset(metadata={"baz": "qux"})
def downstream(upstream):
    return upstream + 1


defs = Definitions(assets=[upstream, downstream])
