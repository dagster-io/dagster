import os

from dagster import Definitions, graph

from .repository_v2 import (
    items,
    stories,
    comments,
    resources,
    clone_prod,
    get_current_env,
)
from .clone_and_drop_db import drop_database_clone

# start_drop_db


@graph
def drop_prod_clone():
    drop_database_clone()


branch_deployment_jobs = [
    clone_prod.to_job(resource_defs=resources[get_current_env()]),
    drop_prod_clone.to_job(resource_defs=resources[get_current_env()]),
]

defs = Definitions(
    assets=[items, comments, stories],
    resources=resources[get_current_env()],
    jobs=(
        branch_deployment_jobs
        if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT") == "1"
        else []
    ),
)


# end_drop_db
