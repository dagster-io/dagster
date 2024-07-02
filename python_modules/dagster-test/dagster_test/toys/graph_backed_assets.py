from dagster import op, graph_asset


@op
def hello():
    return "hello"


@op
def world(hello):
    return hello + "world"


@graph_asset
def graph_backed_asset():
    return world(hello())
