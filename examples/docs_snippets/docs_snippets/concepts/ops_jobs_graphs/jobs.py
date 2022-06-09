# isort: skip_file

# pylint: disable=unused-argument,reimported

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


def do_something(x):
    return x


# start_top_level_input_graph
from dagster import graph, op


@op
def op_with_input(x):
    return do_something(x)


@graph
def wires_input(x):
    op_with_input(x)


# end_top_level_input_graph

# start_top_level_input_job
the_job = wires_input.to_job(input_values={"x": 5})
# end_top_level_input_job

# start_execute_in_process_input
graph_result = wires_input.execute_in_process(input_values={"x": 5})

job_result = the_job.execute_in_process(input_values={"x": 6})  # Overrides existing input value
# end_execute_in_process_input
