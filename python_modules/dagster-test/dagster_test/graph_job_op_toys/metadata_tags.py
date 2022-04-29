from dagster import MetadataValue, job, op


@op
def wow():
    return "so cool!"


@job(
    metadata={
        "foo": "bar",
        "baz": MetadataValue.text("aaaa"),
        "a_link": MetadataValue.url(url="https://dagster.io"),
    },
    tags={"bbb": "ccc"},
    default_run_tags={"aaa": "ddd"},
    job_tags={"owner": "core_team"},
)
def with_tags_and_metadata():
    wow()
