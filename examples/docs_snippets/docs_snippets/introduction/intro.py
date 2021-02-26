from dagster import (
    execute_pipeline,
    make_python_type_usable_as_dagster_type,
    pipeline,
    repository,
    solid,
)
from dagster_pandas import DataFrame as DagsterPandasDataFrame
from pandas import DataFrame

make_python_type_usable_as_dagster_type(python_type=DataFrame, dagster_type=DagsterPandasDataFrame)

# start_intro_0
@solid(description="Calculates the grams of sugar per cup of each kind of cereal.")
def sugar_by_volume(_, cereals: DataFrame) -> DataFrame:
    df = cereals[["name"]].copy()
    df["sugar_per_cup"] = cereals["sugars"] / cereals["cups"]
    return df


@solid(description="Finds the sugar-per-cup cutoff for the top quartile of cereals.")
def top_quartile_cutoff(_, cereals: DataFrame) -> float:
    return cereals["sugar_per_cup"].quantile(0.75)


@solid(description="Selects cereals whose sugar-per-cup exceeds the given cutoff.")
def sugariest_cereals(_, cereals: DataFrame, cutoff: float) -> DataFrame:
    return cereals[cereals["sugar_per_cup"] > cutoff]


@pipeline
def sugariest_pipeline():
    sugar_by_vol = sugar_by_volume()
    sugariest_cereals(sugar_by_vol, top_quartile_cutoff(sugar_by_vol))


# end_intro_0


if __name__ == "__main__":
    result = execute_pipeline(
        sugariest_pipeline,
        run_config={
            "solids": {
                "sugar_by_volume": {"inputs": {"cereals": {"csv": {"path": "cereal.csv"}}}},
                "sugariest_cereals": {
                    "outputs": [{"result": {"csv": {"path": "sugariest_cereal.csv"}}}]
                },
            },
        },
    )


@repository
def intro_repo():
    return [sugariest_pipeline]
