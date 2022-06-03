from dagster import MetadataValue, job, op


@op
def my_op():
    return "so cool!"


@job(
    metadata={
        "owner": "data team",
        "link": MetadataValue.url(url="https://dagster.io"),
    },
)
def with_metadata():
    my_op()
