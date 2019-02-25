import os

import click

from six import string_types

from dagster import check
from dagster.cli.dynamic_loader import pipeline_target_command
from dagster.cli.pipeline import create_pipeline_from_cli_args, REPO_TARGET_WARNING
from dagster.utils import load_yaml_from_glob_list

from .scaffold import scaffold_airflow_dag
from .version import __version__


@click.command(
    name='scaffold',
    help=(
        'Scaffold a dagster pipeline for use with airflow. {warning}'.format(
            warning=REPO_TARGET_WARNING
        )
    ),
)
@click.option(
    '--image', help='The Docker image to use to run your pipeline with airflow.', required=True
)
@pipeline_target_command
@click.option(
    '--install',
    is_flag=True,
    help=(
        'If the --install flag is set, automatically copy the scaffolded DAG files to '
        '$AIRFLOW_HOME. Will error if $AIRFLOW_HOME is not set'
    ),
)
@click.option(
    '-e',
    '--env',
    type=click.STRING,
    multiple=True,
    help=(
        'Specify one or more environment files. These can also be file patterns. '
        'If more than one environment file is captured then those files are merged. '
        'Files listed first take precendence. They will smash the values of subsequent '
        'files at the key-level granularity. If the file is a pattern then you must '
        'enclose it in double quotes'
        '\n\nExample: '
        'dagster-airflow scaffold airline_demo_download_pipeline -e '
        '"environments/download/local_*.yml"'
        '\n\nYou can also specify multiple files:'
        '\n\nExample: '
        'dagster-airflow scaffold airline_demo_download_pipeline -e environments/local_base.yml '
        '-e environments/local_fast_download.yml'
    ),
)
def scaffold(env, install, image, **cli_args):
    check.invariant(isinstance(env, tuple))
    env = list(env)

    check.str_param(image, 'image')

    if install:
        airflow_home = os.getenv('AIRFLOW_HOME')
        check.invariant(isinstance(airflow_home, string_types))
        output_path = os.path.join(os.path.abspath(airflow_home), 'dags')
    else:
        output_path = None

    pipeline = create_pipeline_from_cli_args(cli_args)

    env_config = load_yaml_from_glob_list(env)

    scaffold_airflow_dag(pipeline, env_config, image=image, output_path=output_path)


def create_dagster_airflow_cli():
    @click.group(commands={'scaffold': scaffold})
    @click.version_option(version=__version__)
    def group():
        pass

    return group


def main():
    cli = create_dagster_airflow_cli()
    # click magic
    cli(obj={})  # pylint:disable=unexpected-keyword-arg
