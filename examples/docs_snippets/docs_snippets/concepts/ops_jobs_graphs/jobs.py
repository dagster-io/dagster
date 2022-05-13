# pylint: disable=unused-argument

from dagster import DependencyDefinition, GraphDefinition, job, op


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


@job
def one_plus_one():
    add_one(return_one())


# end_pipeline_example_marker

# start_multiple_usage_pipeline
@job
def multiple_usage():
    add_one(add_one(return_one()))


# end_multiple_usage_pipeline

# start_alias_pipeline
@job
def alias():
    add_one.alias("second_addition")(add_one(return_one()))


# end_alias_pipeline


# start_tag_pipeline
@job
def tagged_add_one():
    add_one.tag({"my_tag": "my_value"})(add_one(return_one()))


# end_tag_pipeline


# start_pipeline_definition_marker
one_plus_one_from_constructor = GraphDefinition(
    name="one_plus_one",
    node_defs=[return_one, add_one],
    dependencies={"add_one": {"number": DependencyDefinition("return_one")}},
).to_job()
# end_pipeline_definition_marker


# start_tags_pipeline
@job(tags={"my_tag": "my_value"})
def my_tags_job():
    my_op()


# end_tags_pipeline
