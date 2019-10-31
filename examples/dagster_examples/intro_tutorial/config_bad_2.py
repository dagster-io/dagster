import csv

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
    with open(csv_path, 'r') as fd:
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

    context.log.info('Read {n_lines} lines'.format(n_lines=len(lines)))

    return lines


@pipeline
def config_pipeline():
    read_csv()


if __name__ == '__main__':
    environment_dict = {
        'solids': {
            'read_csv': {
                'inputs': {
                    'csv_path': {'value': 'cereal.csv'},
                    'delimiter': {'value': ','},
                    'doublequote': {'value': False},
                    'escapechar': {'value': '\\'},
                    'quotechar': {'value': '"'},
                    'quoting': {'value': csv.QUOTE_MINIMAL},
                    'skipinitialspace': {'value': False},
                    'strict': {'value': False},
                }
            }
        }
    }
    result = execute_pipeline(
        config_pipeline, environment_dict=environment_dict
    )
    assert result.success
