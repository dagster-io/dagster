# type: ignore
# start_asset
# This would be the python code living in a shared module.
from shared_module import my_shared_python_callable

from dagster import asset


@asset
def my_shared_asset():
    return my_shared_python_callable()


# end_asset
