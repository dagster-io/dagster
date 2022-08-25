from dagster import AssetsDefinition, graph, op
from dagster._legacy import AssetGroup


@op
def hello():
    return "hello"


@op
def world(hello):
    return hello + "world"


@graph
def hello_world():
    return world(hello())


graph_asset = AssetsDefinition.from_graph(hello_world, group_name="hello_world_group")

graph_backed_group = AssetGroup([graph_asset])
