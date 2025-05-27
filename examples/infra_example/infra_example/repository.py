from dagster import repository

from .jobs.resource_infra_example import resource_infra_example
from .jobs.tag_infra_example import tag_infra_example


@repository
def infra_example():
    jobs = [resource_infra_example, tag_infra_example]

    return jobs
