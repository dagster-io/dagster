from dagster import graph, op


@op(config_schema={"param": str})
def do_something(_):
    ...


@graph
def do_it_all():
    do_something()


do_it_all_job = do_it_all.to_job(
    config={"solids": {"do_something": {"config": {"param": "some_val"}}}}
)
