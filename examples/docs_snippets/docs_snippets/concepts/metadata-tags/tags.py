from dagster import asset, define_asset_job, graph, job, op, to_job

# start_asset_tags


@asset(tags={"domain": "marketing", "pii": "true"})
def leads(): ...


# end_asset_tags

# start_asset_job_tags

asset_job = define_asset_job(
    name="marketing_job", selection="*", tags={"dagster/max_runtime": 10}
)

# end_asset_job_tags


@op
def send_email(): ...


# start_op_job_tags


@job(tags={"domain": "marketing"})
def email_job():
    send_email()


# end_op_job_tags


@graph
def email_graph():
    send_email()


# start_tags_on_graph_to_job

my_second_job_with_tags = email_graph.to_job(tags={"domain": "marketing"})

# end_tags_on_graph_to_job
