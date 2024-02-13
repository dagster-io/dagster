# ruff: noqa
from dagster import Definitions

from .resources import DataGeneratorResource

# start_add_config_to_resource
from dagster import (
    # .. your existing imports go here
    EnvVar,
)

# ... the existing portion of your `__init__.py` goes here.

# Configure the resource with an environment variable here
datagen = DataGeneratorResource(
    num_days=EnvVar.int("HACKERNEWS_NUM_DAYS_WINDOW"),
)

defs = Definitions(
    # ...
    resources={"hackernews_api": datagen}
)
# end_add_config_to_resource
