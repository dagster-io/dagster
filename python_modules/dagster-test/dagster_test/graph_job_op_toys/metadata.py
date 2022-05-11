from dagster import MetadataValue, job, op


@op
def wow():
    return "so cool!"


@job(
    metadata={
        "owner": "core",
        "foo": MetadataValue.text("bar"),
        "link": MetadataValue.url(url="https://dagster.io"),
    },
)
def with_metadata():
    wow()
