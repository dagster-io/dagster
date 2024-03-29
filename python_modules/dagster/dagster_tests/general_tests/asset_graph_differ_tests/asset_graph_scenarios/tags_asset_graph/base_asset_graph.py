from dagster import Definitions, asset


@asset(tags={"foo": "bar"})
def upstream():
    return 1


@asset(tags={"baz": "qux"})
def downstream(upstream):
    return upstream + 1


defs = Definitions(assets=[upstream, downstream])
