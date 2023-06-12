from dagster import Definitions, EnvVar

from .resources import DataGeneratorResource

# start_add_config_to_resource
datagen = DataGeneratorResource(
    num_days=EnvVar.int("HACKERNEWS_NUM_DAYS_WINDOW"),
)

defs = Definitions(
    # ...
    resources={"hackernews_api": datagen}
)
# end_add_config_to_resource
