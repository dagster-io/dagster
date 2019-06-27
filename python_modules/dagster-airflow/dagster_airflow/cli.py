import contextlib
import os
import sys

import click
import yaml

from dagster.utils.indenting_printer import IndentingStringIoPrinter

if sys.version_info.major >= 3:
    from io import StringIO  # pylint:disable=import-error
else:
    from StringIO import StringIO  # pylint:disable=import-error


def _construct_yml(environment_yaml_file, dag_name):
    environment_dict = {}
    if environment_yaml_file is not None:
        with open(environment_yaml_file, 'rb') as f:
            environment_dict = yaml.safe_load(f)

    if 'storage' not in environment_dict:
        environment_dict['storage'] = {
            'filesystem': {'config': {'base_dir': '/tmp/dagster-airflow/{}'.format(dag_name)}}
        }

    # See http://bit.ly/309sTOu
    with contextlib.closing(StringIO()) as f:
        yaml.dump(environment_dict, f, default_flow_style=False, allow_unicode=True)
        return f.getvalue()


@click.group()
def main():
    pass


@main.command()
@click.option('--dag-name', help='The name of the output Airflow DAG', required=True)
@click.option('--module-name', '-m', help='The name of the source module', required=True)
@click.option('--pipeline-name', '-n', help='The name of the pipeline', required=True)
@click.option(
    '--output-path',
    '-o',
    help='Optional. If unset, $AIRFLOW_HOME will be used.',
    default=os.getenv('AIRFLOW_HOME'),
)
@click.option(
    '--environment-file',
    '-c',
    help='''Optional. Path to a YAML file to install into the Dagster environment.''',
)
def scaffold(dag_name, module_name, pipeline_name, output_path, environment_file):
    '''Creates a DAG file for a specified dagster pipeline'''

    # Validate output path
    if not output_path:
        raise Exception('You must specify --output-path or set AIRFLOW_HOME to use this script.')

    # We construct the YAML environment and then put it directly in the DAG file
    environment_yaml = _construct_yml(environment_file, dag_name)

    printer = IndentingStringIoPrinter(indent_level=4)
    printer.line('\'\'\'')
    printer.line(
        'The airflow DAG scaffold for {module_name}.{pipeline_name}'.format(
            module_name=module_name, pipeline_name=pipeline_name
        )
    )
    printer.blank_line()
    printer.line('Note that this docstring must contain the strings "airflow" and "DAG" for')
    printer.line('Airflow to properly detect it as a DAG')
    printer.line('See: http://bit.ly/307VMum')
    printer.line('\'\'\'')
    printer.line('import datetime')
    printer.line('import yaml')
    printer.blank_line()
    printer.line('from dagster_airflow.factory import make_airflow_dag')
    printer.blank_line()
    printer.blank_line()
    printer.line('ENVIRONMENT = \'\'\'')
    printer.line(environment_yaml)
    printer.line('\'\'\'')
    printer.blank_line()
    printer.blank_line()
    printer.comment('NOTE: these arguments should be edited for your environment')
    printer.line('DEFAULT_ARGS = {')
    with printer.with_indent():
        printer.line("'owner': 'airflow',")
        printer.line("'depends_on_past': False,")
        printer.line("'start_date': datetime.datetime(2019, 5, 7),")
        printer.line("'email': ['airflow@example.com'],")
        printer.line("'email_on_failure': False,")
        printer.line("'email_on_retry': False,")
    printer.line('}')
    printer.blank_line()
    printer.line('dag, tasks = make_airflow_dag(')
    with printer.with_indent():
        printer.comment(
            'NOTE: you must ensure that {module_name} is installed or available on sys.path, '
            'otherwise, this import will fail.'.format(module_name=module_name)
        )
        printer.line('module_name=\'{module_name}\','.format(module_name=module_name))
        printer.line('pipeline_name=\'{pipeline_name}\','.format(pipeline_name=pipeline_name))
        printer.line("environment_dict=yaml.load(ENVIRONMENT),")
        printer.line("dag_kwargs={'default_args': DEFAULT_ARGS, 'max_active_runs': 1}")
    printer.line(')')

    # Ensure output_path/dags exists
    dags_path = os.path.join(output_path, 'dags')
    if not os.path.isdir(dags_path):
        os.makedirs(dags_path)

    dag_file = os.path.join(output_path, 'dags', dag_name + '.py')
    with open(dag_file, 'wb') as f:
        f.write(printer.read().encode())


if __name__ == '__main__':
    main()  # pylint:disable=no-value-for-parameter
