from dagster import asset, define_asset_job, job, to_job

# start_asset_tags


@asset(tags={"domain": "marketing", "pii": "true"})
def leads():
    ...


# end_asset_tags

# start_asset_job_tags

asset_job = define_asset_job(
    name="marketing_job", selection="*", tags={"dagster/max_runtime": 10}
)

# end_asset_job_tags

# start_op_job_tags


@job(tags={"foo": "bar"})
def my_job_with_tags():
    my_op()


# end_op_job_tags

# start_tags_on_graph_to_job

my_second_job_with_tags = my_graph.to_job(tags={"foo": "bar"})

# end_tags_on_graph_to_job
