import dagster as dg
from project_mini.defs.resource_caching.expensive_resource import ExpensiveResource
from project_mini.defs.resource_caching.expensive_resource_cache import ExpensiveResourceCache
from project_mini.defs.resource_caching.expensive_resource_pickle import ExpensiveResourcePickle


@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "expensive_resource": ExpensiveResource(),
            "expensive_resource_cache": ExpensiveResourceCache(),
            "expensive_resource_pickle": ExpensiveResourcePickle(),
        }
    )
