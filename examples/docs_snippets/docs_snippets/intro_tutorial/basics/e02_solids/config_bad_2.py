import csv
import os

from dagster import execute_pipeline, pipeline, solid


@solid
def read_csv(
    context,
    csv_path,
    delimiter,
    doublequote,
    escapechar,
    quotechar,
    quoting,
    skipinitialspace,
    strict,
):
    csv_path = os.path.join(os.path.dirname(__file__), csv_path)
    with open(csv_path, "r") as fd:
        lines = [
            row
            for row in csv.DictReader(
                fd,
                delimiter=delimiter,
                doublequote=doublequote,
                escapechar=escapechar,
                quotechar=quotechar,
                quoting=quoting,
                skipinitialspace=skipinitialspace,
                strict=strict,
            )
        ]

    context.log.info("Read {n_lines} lines".format(n_lines=len(lines)))

    return lines


@pipeline
def config_pipeline():
    read_csv()


if __name__ == "__main__":
    run_config = {
        "solids": {
            "read_csv": {
                "inputs": {
                    "csv_path": {"value": "cereal.csv"},
                    "delimiter": {"value": ","},
                    "doublequote": {"value": False},
                    "escapechar": {"value": "\\"},
                    "quotechar": {"value": '"'},
                    "quoting": {"value": csv.QUOTE_MINIMAL},
                    "skipinitialspace": {"value": False},
                    "strict": {"value": False},
                }
            }
        }
    }
    result = execute_pipeline(config_pipeline, run_config=run_config)
    assert result.success
