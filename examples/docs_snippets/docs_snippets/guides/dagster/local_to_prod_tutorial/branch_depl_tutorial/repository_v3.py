from dagster import repository, with_resources, graph
from .repository_v2 import items, comments, stories, resource_defs, clone_prod, get_current_env
from .clone_and_drop_db import drop_database_clone

# start_drop_db


@graph
def drop_prod_clone():
    drop_database_clone()


@repository
def repo():
    ...
    return [
        with_resources([items, comments, stories], resource_defs=resource_defs[get_current_env()]),
        clone_prod.to_job(resource_defs=resource_defs[get_current_env()]),
        drop_prod_clone.to_job(resource_defs=resource_defs[get_current_env()]),
    ]


# end_drop_db
