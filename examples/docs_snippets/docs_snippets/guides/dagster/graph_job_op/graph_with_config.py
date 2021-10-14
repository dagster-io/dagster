from dagster import job, op


@op(config_schema={"param": str})
def do_something(_):
    ...


@job(
    config={
        "ops": {
            "do_something": {
                "config": {
                    "param": "some_val",
                }
            }
        }
    }
)
def do_it_all():
    do_something()
