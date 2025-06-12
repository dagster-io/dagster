import dagster as dg

from mlops_demo import deployment, inference, ingestion, resources, training
from mlops_demo.ingestion import (
    get_all_readings_job,
    min_number_of_machine_statuses_sensor,
    min_number_of_readings_sensor,
)
from mlops_demo.training import train_ml_model_job, train_ml_model_schedule

all_assets = dg.load_assets_from_modules([ingestion, training, deployment, inference])

defs = dg.Definitions(
    assets=all_assets,
    resources={"rmqconn": resources.rabbitmq_connection_resource.configured({"host": "localhost"})},
    jobs=[get_all_readings_job, train_ml_model_job],
    sensors=[min_number_of_readings_sensor, min_number_of_machine_statuses_sensor],
    schedules=[train_ml_model_schedule],
)
