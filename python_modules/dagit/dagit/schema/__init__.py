from __future__ import absolute_import
from dagster_graphql import dauphin


def create_schema():
    # dauphin depends on import-based side effects
    # pylint: disable=W0611
    from dagster_graphql.schema import (
        config_types,
        errors,
        execution,
        paging,
        pipelines,
        runs,
        runtime_types,
    )
    from dagit.schema import roots

    return dauphin.create_schema()
