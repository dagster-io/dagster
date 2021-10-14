# pylint: disable=unused-argument

from dagster import DependencyDefinition, GraphDefinition, graph, op


@op
def my_op():
    pass


# start_pipeline_example_marker
@op
def return_one(context):
    return 1


@op
def add_one(context, number: int):
    return number + 1


@graph
def one_plus_one():
    add_one(return_one())


# end_pipeline_example_marker

# start_multiple_usage_pipeline
@graph
def multiple_usage():
    add_one(add_one(return_one()))


# end_multiple_usage_pipeline

# start_alias_pipeline
@graph
def alias():
    add_one.alias("second_addition")(add_one(return_one()))


# end_alias_pipeline


# start_tag_pipeline
@graph
def tagged_add_one():
    add_one.tag({"my_tag": "my_value"})(add_one(return_one()))


# end_tag_pipeline


# start_pipeline_definition_marker
one_plus_one_graph_def = GraphDefinition(
    name="one_plus_one",
    node_defs=[return_one, add_one],
    dependencies={"add_one": {"number": DependencyDefinition("return_one")}},
)
# end_pipeline_definition_marker


# start_tags_pipeline
@graph(tags={"my_tag": "my_value"})
def my_tags_pipeline():
    my_op()


# end_tags_pipeline
