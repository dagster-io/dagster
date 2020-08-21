import os

import pandas


def load_cereals():
    path_to_csv = os.path.join(os.path.dirname(__file__), "data/cereal.csv")
    return pandas.read_csv(path_to_csv)


def add_sugar_per_cup(cereals):
    df = cereals[["name"]]
    df["sugar_per_cup"] = cereals["sugars"] / cereals["cups"]
    return df


def compute_cutoff(cereals):
    return cereals["sugar_per_cup"].quantile(0.75)


def filter_below_cutoff(cereals, cutoff):
    return cereals[cereals["sugar_per_cup"] > cutoff]


def write_sugariest(cereals):
    cereals.to_csv("/tmp/top_quartile.csv")
    return cereals


def compute_top_quartile():
    with_per_cup = add_sugar_per_cup(load_cereals())
    return write_sugariest(
        filter_below_cutoff(cereals=with_per_cup, cutoff=compute_cutoff(with_per_cup))
    )
