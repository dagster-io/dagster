import os

from dagster import graph, repository, with_resources

from .clone_and_drop_db import drop_database_clone
from .repository_v2 import (
    clone_prod,
    comments,
    get_current_env,
    items,
    resource_defs,
    stories,
)

# start_drop_db


@graph
def drop_prod_clone():
    drop_database_clone()


@repository
def repo():
    ...
    branch_deployment_jobs = [
        clone_prod.to_job(resource_defs=resource_defs[get_current_env()]),
        drop_prod_clone.to_job(resource_defs=resource_defs[get_current_env()]),
    ]
    return [
        with_resources(
            [items, comments, stories], resource_defs=resource_defs[get_current_env()]
        ),
        *(
            branch_deployment_jobs
            if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT")
            else []
        ),
    ]


# end_drop_db
