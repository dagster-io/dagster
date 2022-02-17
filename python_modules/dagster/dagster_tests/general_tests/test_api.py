import inspect

import dagster


def test_all():
    dagster_dir = dir(dagster)
    for each in dagster.__all__:
        assert each in dagster_dir
    for exported in dagster_dir:
        if not exported.startswith("_") and not inspect.ismodule(getattr(dagster, exported)):
            assert exported in dagster.__all__
