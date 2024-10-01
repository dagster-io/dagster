from dagster import Definitions, asset


@asset(code_version="1")
def upstream():
    return 1


@asset(code_version="2")
def downstream():
    return 2


defs = Definitions(assets=[upstream, downstream])
