from dagster import (
    job,
    MetadataEntry,
    MetadataValue
)

from .ops import does_nothing

@job(
    metadata=[
        MetadataEntry.text(label="team", value="core", searchable=True)
    ]
)
def job_with_searchable_metadata():
    does_nothing()