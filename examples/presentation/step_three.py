# Step two adds solids and pipelines
# Can demonstrate viewer
import os
import time

import pandas

from dagster import Field, pipeline, solid


@solid
def load_cereals(_):
    path_to_csv = os.path.join(os.path.dirname(__file__), "data/cereal.csv")
    return pandas.read_csv(path_to_csv)


@solid(
    description="Augments dataframe with a `sugar_per_cup` column.",
    config_schema={
        "delay": Field(
            float,
            default_value=1.0,
            is_required=False,
            description="Number of seconds of computation to simulate",
        )
    },
)
def add_sugar_per_cup(context, cereals):
    delay = context.solid_config["delay"]
    context.log.info("Simulating computation for {sec} seconds!".format(sec=delay))
    time.sleep(delay)
    df = cereals[["name"]]
    df["sugar_per_cup"] = cereals["sugars"] / cereals["cups"]
    return df


@solid(
    description="Computes a float value that cuts off the top 25 percent of `sugar_per_cup`",
    config_schema={
        "delay": Field(
            float,
            default_value=1.0,
            is_required=False,
            description="Number of seconds of computation to simulate",
        )
    },
)
def compute_cutoff(context, cereals):
    time.sleep(context.solid_config["delay"])
    return cereals["sugar_per_cup"].quantile(0.75)


@solid(
    description="Filter out all cereals whose `sugar_per_cup` is below the provided cutoff value",
    config_schema={
        "delay": Field(
            float,
            default_value=1.0,
            is_required=False,
            description="Number of seconds of computation to simulate",
        )
    },
)
def filter_below_cutoff(context, cereals, cutoff):
    time.sleep(context.solid_config["delay"])
    foo = cereals[cereals["sugar_per_cup"] > cutoff]
    return foo


@solid
def write_sugariest(_, cereals):
    cereals.to_csv("/tmp/top_quartile.csv")


@pipeline
def compute_top_quartile_pipeline():
    with_per_cup = add_sugar_per_cup(load_cereals())
    write_sugariest(filter_below_cutoff(cereals=with_per_cup, cutoff=compute_cutoff(with_per_cup)))


from dagster import repository  # isort:skip


@repository
def step_three_repo():
    return [compute_top_quartile_pipeline]
