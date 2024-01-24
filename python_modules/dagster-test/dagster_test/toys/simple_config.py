from dagster import job, op


@op(
    config_schema={"num": int},
)
def requires_config(context):
    return context.op_config


@job(
    tags={
        "dagster-k8s/config": {
            "container_config": {
                "resources": {
                    "requests": {"cpu": "3"},
                },
            }
        }
    },
)
def simple_config_job():
    requires_config()
