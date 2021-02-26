import csv
import os

from dagster import execute_pipeline, pipeline, solid


@solid
def read_csv(context, csv_path):
    csv_path = os.path.join(os.path.dirname(__file__), csv_path)
    with open(csv_path, "r") as fd:
        lines = [row for row in csv.DictReader(fd)]

    context.log.info("Read {n_lines} lines".format(n_lines=len(lines)))
    return lines


# start_config_marker_0
@solid(config_schema={"reverse": bool})
def sort_by_calories(context, cereals):
    sorted_cereals = sorted(
        cereals,
        key=lambda cereal: int(cereal["calories"]),
        reverse=context.solid_config["reverse"],
    )

    if context.solid_config["reverse"]:  # find the most caloric cereal
        context.log.info(
            "{x} caloric cereal: {first_cereal_after_sort}".format(
                x="Most", first_cereal_after_sort=sorted_cereals[0]["name"]
            )
        )
        return {
            "most_caloric": sorted_cereals[0],
            "least_caloric": sorted_cereals[-1],
        }
    else:  # find the least caloric cereal
        context.log.info(
            "{x} caloric cereal: {first_cereal_after_sort}".format(
                x="Least", first_cereal_after_sort=sorted_cereals[0]["name"]
            )
        )
        return {
            "least_caloric": sorted_cereals[0],
            "most_caloric": sorted_cereals[-1],
        }


# end_config_marker_0


@pipeline
def config_pipeline():
    sort_by_calories(read_csv())


if __name__ == "__main__":
    # start_config_marker_1
    run_config = {
        "solids": {
            "read_csv": {"inputs": {"csv_path": {"value": "cereal.csv"}}},
            "sort_by_calories": {"config": {"reverse": True}},
        }
    }
    # end_config_marker_1

    # start_config_marker_2
    result = execute_pipeline(config_pipeline, run_config=run_config)
    # end_config_marker_2
    assert result.success
