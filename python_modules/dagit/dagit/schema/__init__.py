from __future__ import absolute_import
from dagster_graphql import dauphin


def create_schema():
    # dauphin depends on import-based side effects
    # pylint: disable=W0611
    from dagit.schema import (
        config_types,
        errors,
        execution,
        generic,
        pipelines,
        roots,
        runtime_types,
        runs,
    )

    return dauphin.create_schema()
