from dagster import MetadataValue, graph, job, op

# start_metadata_on_job


@op
def my_op():
    return "Hello World!"


@job(
    metadata={
        "owner": "data team",  # will be converted to MetadataValue.text
        "docs": MetadataValue.url("https://docs.dagster.io"),
    }
)
def my_job_with_metadata():
    my_op()


# end_metadata_on_job


# start_metadata_on_graph_to_job


@graph
def my_graph():
    my_op()


my_second_job_with_metadata = my_graph.to_job(
    metadata={"owner": "api team", "docs": MetadataValue.url("https://docs.dagster.io")}
)

# end_metadata_on_graph_to_job

# start_tags_on_job


@job(tags={"foo": "bar"})
def my_job_with_tags():
    my_op()


# end_tags_on_job

# start_tags_on_graph_to_job

my_second_job_with_tags = my_graph.to_job(tags={"foo": "bar"})

# end_tags_on_graph_to_job
