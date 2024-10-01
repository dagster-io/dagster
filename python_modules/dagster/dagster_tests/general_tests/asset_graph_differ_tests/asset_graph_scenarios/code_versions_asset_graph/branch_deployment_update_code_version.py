from dagster import Definitions, asset


@asset(code_version="2")
def upstream():
    return 1


@asset(code_version="1")
def downstream(upstream):
    return upstream + 1


defs = Definitions(assets=[upstream, downstream])
