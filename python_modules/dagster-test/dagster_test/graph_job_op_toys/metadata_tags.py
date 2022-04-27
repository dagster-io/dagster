from dagster import MetadataValue, job, op


@op
def wow():
    return "so cool!"


@job(
    metadata={
        "foo": "bar",
        "baz": MetadataValue.text("aaaa"),
        "not_shown": MetadataValue.url(url="https://dagster.io"),
    },
    tags={"bbb": "ccc"},
)
def wow_job():
    wow()
