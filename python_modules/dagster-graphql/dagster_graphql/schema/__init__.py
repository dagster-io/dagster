from __future__ import absolute_import

from dagster_graphql import dauphin


def create_schema():
    # dauphin depends on import-based side effects
    # pylint: disable=W0611
    from . import (
        assets,
        config_types,
        dagster_types,
        errors,
        execution,
        external,
        paging,
        partition_sets,
        pipelines,
        roots,
        runs,
        schedules,
    )

    return dauphin.create_schema()
