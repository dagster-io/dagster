from dagster import Definitions

from .resources import DataGeneratorResource

# start_add_config_to_resource
datagen = DataGeneratorResource(num_days=365)

defs = Definitions(
    # ...
    resources={"hackernews_api": datagen}
)
# end_add_config_to_resource
