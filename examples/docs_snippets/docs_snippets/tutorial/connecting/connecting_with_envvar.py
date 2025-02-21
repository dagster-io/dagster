# ruff: noqa
from dagster import Definitions

from .resources import DataGeneratorResource

# start_add_config_to_resource
import dagster as dg


# ... the dg.existing portion of dg.your `definitions.py` goes dg.here.

# Configure the resource with an environment variable dg.here
datagen = DataGeneratorResource(
    num_days=dg.EnvVar.int("HACKERNEWS_NUM_DAYS_WINDOW"),
)

defs = Definitions(
    # ...
    resources={"hackernews_api": datagen}
)
# end_add_config_to_resource
