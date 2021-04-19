import csv
import os

import requests
from dagster import (
    AssetMaterialization,
    EventMetadataEntry,
    Output,
    execute_pipeline,
    pipeline,
    solid,
)


@solid
def download_csv(context, url):
    response = requests.get(url)
    lines = response.text.split("\n")
    context.log.info("Read {n_lines} lines".format(n_lines=len(lines)))
    return [row for row in csv.DictReader(lines)]


# start_materializations_marker_0
@solid
def sort_by_calories(context, cereals):
    sorted_cereals = sorted(
        cereals, key=lambda cereal: int(cereal["calories"])
    )
    context.log.info(
        "Least caloric cereal: {least_caloric}".format(
            least_caloric=sorted_cereals[0]["name"]
        )
    )
    context.log.info(
        "Most caloric cereal: {most_caloric}".format(
            most_caloric=sorted_cereals[-1]["name"]
        )
    )
    fieldnames = list(sorted_cereals[0].keys())
    sorted_cereals_csv_path = os.path.abspath(
        "output/calories_sorted_{run_id}.csv".format(run_id=context.run_id)
    )
    os.makedirs(os.path.dirname(sorted_cereals_csv_path), exist_ok=True)
    with open(sorted_cereals_csv_path, "w") as fd:
        writer = csv.DictWriter(fd, fieldnames)
        writer.writeheader()
        writer.writerows(sorted_cereals)
    yield AssetMaterialization(
        asset_key="sorted_cereals_csv",
        description="Cereals data frame sorted by caloric content",
        metadata_entries=[
            EventMetadataEntry.path(
                sorted_cereals_csv_path, "sorted_cereals_csv_path"
            )
        ],
    )
    yield Output(None)


# end_materializations_marker_0


@pipeline
def materialization_pipeline():
    sort_by_calories(download_csv())


if __name__ == "__main__":
    run_config = {
        "solids": {
            "download_csv": {
                "inputs": {
                    "url": {
                        "value": "https://raw.githubusercontent.com/dagster-io/dagster/master/examples/docs_snippets/docs_snippets/intro_tutorial/cereal.csv"
                    }
                }
            }
        }
    }
    result = execute_pipeline(materialization_pipeline, run_config=run_config)
    assert result.success
