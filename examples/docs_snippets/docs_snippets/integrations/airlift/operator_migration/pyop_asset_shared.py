# This would be the python code living in a shared module.
from dagster import asset

from .shared import my_shared_python_callable


@asset
def my_shared_asset():
    return my_shared_python_callable()
