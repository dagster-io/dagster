import csv
import os

from dagster import (
    DagsterInstance,
    execute_pipeline,
    pipeline,
    reexecute_pipeline,
    solid,
)


@solid
def read_csv(context, csv_path: str) -> list:
    csv_path = os.path.join(os.path.dirname(__file__), csv_path)
    with open(csv_path, "r") as fd:
        lines = [row for row in csv.DictReader(fd)]

    context.log.info("Read {n_lines} lines".format(n_lines=len(lines)))
    return lines


@solid
def sort_by_calories(context, cereals: list):
    sorted_cereals = sorted(cereals, key=lambda cereal: cereal["calories"])
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
    return sorted_cereals


@pipeline
def reexecution_pipeline():
    sort_by_calories(read_csv())


if __name__ == "__main__":
    run_config = {
        "solids": {
            "read_csv": {
                "inputs": {"csv_path": {"value": "../../cereal.csv"}}
            }
        },
        "storage": {"filesystem": {}},
    }
    instance = DagsterInstance.ephemeral()
    result = execute_pipeline(
        reexecution_pipeline, run_config=run_config, instance=instance
    )

    assert result.success

    # skip 'read_csv' and only re-execute step 'sort_by_calories.compute'
    reexecution_result = reexecute_pipeline(
        reexecution_pipeline,
        parent_run_id=result.run_id,
        step_keys_to_execute=["sort_by_calories.compute"],
        instance=instance,
        run_config=run_config,
    )
    assert reexecution_result.success
