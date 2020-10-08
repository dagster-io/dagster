# Step two adds solids and pipelines
# Can demonstrate viewer
import os

import pandas

from dagster import pipeline, solid


@solid
def load_cereals(_):
    path_to_csv = os.path.join(os.path.dirname(__file__), "data/cereal.csv")
    return pandas.read_csv(path_to_csv)


@solid
def add_sugar_per_cup(_, cereals):
    df = cereals[["name"]]
    df["sugar_per_cup"] = cereals["sugars"] / cereals["cups"]
    return df


@solid
def compute_cutoff(_, cereals):
    return cereals["sugar_per_cup"].quantile(0.75)


@solid
def filter_below_cutoff(_, cereals, cutoff):
    foo = cereals[cereals["sugar_per_cup"] > cutoff]
    return foo


@solid
def write_sugariest(_, cereals):
    cereals.to_csv("/tmp/top_quartile.csv")


@pipeline
def compute_top_quartile_pipeline_step_two():
    with_per_cup = add_sugar_per_cup(load_cereals())
    write_sugariest(filter_below_cutoff(cereals=with_per_cup, cutoff=compute_cutoff(with_per_cup)))


from dagster import repository  # isort:skip


@repository
def step_two_repo():
    return [compute_top_quartile_pipeline_step_two]
