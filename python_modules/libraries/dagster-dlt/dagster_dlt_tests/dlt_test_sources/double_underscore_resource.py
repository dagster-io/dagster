"""Test dlt source with a resource name containing double underscores.

Used to reproduce https://github.com/dagster-io/dagster/issues/33573, where
extract_resource_metadata silently returns empty metadata for resource names that
contain ``__`` because normalize_table_identifier transforms them to a different string.
"""

import dlt

MOCK_DATA = [
    {"id": 1, "value": "alpha"},
    {"id": 2, "value": "beta"},
    {"id": 3, "value": "gamma"},
]


@dlt.source
def pipeline_double_underscore():
    @dlt.resource(
        name="my__test__resource",
        primary_key="id",
        write_disposition="merge",
    )
    def my__test__resource():
        yield from MOCK_DATA

    return (my__test__resource,)
