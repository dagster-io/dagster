from dagster import Definitions, load_assets_from_modules

from . import assets
from .jobs import question_job, search_index_job
from .resources import openai_resource
from .sensors import question_sensor

all_assets = load_assets_from_modules([assets])
all_jobs = [question_job, search_index_job]
all_sensors = [question_sensor]

defs = Definitions(
    assets=all_assets,
    jobs=all_jobs,
    resources={
        "openai": openai_resource,
    },
    sensors=all_sensors,
)
