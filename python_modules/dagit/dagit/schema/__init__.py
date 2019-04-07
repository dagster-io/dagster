from __future__ import absolute_import
from dagster_graphql import dauphin


def create_schema():
    # dauphin depends on import-based side effects
    # pylint: disable=W0611
    from dagster_graphql.schema import config_types, runtime_types, pipelines
    from dagit.schema import errors, execution, generic, roots, runs

    return dauphin.create_schema()
