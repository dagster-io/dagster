from dagster import solid
from dagster_dask.executor import get_dask_resource_requirements


def test_resource_tags():
    @solid(tags={"dagster-dask/resource_requirements": {"GPU": 1, "MEMORY": 10e9}})
    def boop(_):
        pass

    reqs = get_dask_resource_requirements(boop.tags)
    assert reqs["GPU"] == 1
    assert reqs["MEMORY"] == 10e9
