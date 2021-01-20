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
        jobs,
        paging,
        partition_sets,
        pipelines,
        roots,
        runs,
        schedules,
        sensors,
    )

    return dauphin.create_schema()
