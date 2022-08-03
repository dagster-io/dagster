from dagster import asset, repository
from dagster import asset, op, job, repository, define_asset_job, graph
import requests
import csv
import os

MAX_NUM_CEREALS = 100


@asset(config_schema={"num_cereals": int})
def cereals(context):
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    return [row for row in csv.DictReader(lines)][: context.config["num_cereals"]]


@op(config_schema={"op_config": int})
def my_op(context):
    context.log.info("op_config")
    return 1


@graph
def run_op():
    my_op()


@repository
def my_repo():
    config_by_env = {
        "local": {
            "run_op": {"ops": {"my_op": {"config": {"op_config": 1}}}},
            "cereals_job": {"ops": {"cereals": {"config": {"num_cereals": 5}}}},
        },
        "prod": {
            "run_op": {"ops": {"my_op": {"config": {"op_config": 3}}}},
            "cereals_job": {"ops": {"cereals": {"config": {"num_cereals": MAX_NUM_CEREALS}}}},
        },
    }
    return [
        cereals,
        define_asset_job(
            "cereals_job",
            config=config_by_env[os.getenv("DAGSTER_DEPLOYMENT", "local")]["cereals_job"],
        ),
        run_op.to_job(config=config_by_env[os.getenv("DAGSTER_DEPLOYMENT", "local")]["run_op"]),
    ]
