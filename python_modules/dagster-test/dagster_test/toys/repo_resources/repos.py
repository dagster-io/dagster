from .some_graph import bar, bar_schedule
from .some_other_graph import other_bar, other_bar_schedule
from dagster import repository, ResourceDefinition

all_graphs = [bar, other_bar]
all_schedules = [bar_schedule, other_bar_schedule]


@repository
def dev_repo():
    dev_resources = {"abc": ResourceDefinition.hardcoded_resource("dev")}
    return all_schedules + [graph.to_job(resource_defs=dev_resources) for graph in all_graphs]


@repository
def prod_repo():
    prod_resources = {"abc": ResourceDefinition.hardcoded_resource("prod")}
    return all_schedules + [graph.to_job(resource_defs=prod_resources) for graph in all_graphs]
