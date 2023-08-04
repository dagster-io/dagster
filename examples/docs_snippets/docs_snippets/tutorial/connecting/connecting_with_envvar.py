# ruff: noqa: I001
from .resources import DataGeneratorResource

# start_add_config_to_resource
from dagster import Definitions, EnvVar

# ... existing code is here

datagen = DataGeneratorResource(
    num_days=EnvVar.int("HACKERNEWS_NUM_DAYS_WINDOW"),
)

defs = Definitions(
    # ...
    resources={"hackernews_api": datagen}
)
# end_add_config_to_resource
