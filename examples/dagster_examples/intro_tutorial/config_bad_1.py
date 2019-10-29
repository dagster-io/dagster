import csv

from dagster import execute_pipeline, pipeline, solid


@solid
def read_csv(context, csv_path):
    with open(csv_path, 'r') as fd:
        lines = [
            row
            for row in csv.DictReader(
                fd,
                delimiter=',',
                doublequote=False,
                escapechar='\\',
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL,
                skipinitialspace=False,
                strict=False,
            )
        ]

    context.log.info('Read {n_lines} lines'.format(n_lines=len(lines)))

    return lines


@pipeline
def config_pipeline():
    read_csv()


if __name__ == '__main__':
    environment_dict = {
        'solids': {
            'read_csv': {'inputs': {'csv_path': {'value': 'cereal.csv'}}}
        }
    }
    result = execute_pipeline(
        config_pipeline, environment_dict=environment_dict
    )
    assert result.success
