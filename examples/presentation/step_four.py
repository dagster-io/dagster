# Step two adds solids and pipelines
# Can demonstrate viewer
from dagster import repository, file_relative_path, PresetDefinition  # isort:skip


def get_in_repo_preset_definition():
    return PresetDefinition(
        "in_repo",
        run_config={
            "solids": {
                "add_sugar_per_cup": {
                    "inputs": {
                        "cereals": {
                            "csv": {"path": file_relative_path(__file__, "data/cereal.csv")}
                        }
                    }
                }
            },
            "execution": {"multiprocess": {}},
            "storage": {"filesystem": {}},
        },
    )


from dagster import pipeline, solid
from dagster_pandas import DataFrame


@solid
def add_sugar_per_cup(_, cereals: DataFrame) -> DataFrame:
    df = cereals[["name"]]
    df["sugar_per_cup"] = cereals["sugars"] / cereals["cups"]
    return df


@solid
def compute_cutoff(_, cereals: DataFrame) -> float:
    return cereals["sugar_per_cup"].quantile(0.75)


@solid
def filter_below_cutoff(_, cereals: DataFrame, cutoff: float) -> DataFrame:
    return cereals[cereals["sugar_per_cup"] > cutoff]


@pipeline(preset_defs=[get_in_repo_preset_definition()])
def compute_top_quartile_pipeline():
    with_per_cup = add_sugar_per_cup()
    filter_below_cutoff(cereals=with_per_cup, cutoff=compute_cutoff(with_per_cup))


@repository
def step_four_repo():
    return [compute_top_quartile_pipeline]
