import importlib

import click
import yaml

import check


def _load_pipeline_config(pipelines_yml):
    with open(pipelines_yml, 'r') as ff:
        return yaml.load(ff)


@click.command(name='list')
@click.option(
    '--pipelines',
    type=click.Path(file_okay=True, dir_okay=False, exists=True),
    default='pipelines.yml'
)
def dagster_list_commmand(pipelines):
    pipelines_config = _load_pipeline_config(pipelines)

    pipelines = create_pipelines_from_config_object(pipelines_config)

    for pipeline in pipelines:
        print('Pipeline: {name}'.format(name=pipeline.name))


def create_pipelines_from_config_object(pipelines_config):
    pipelines = []

    pipeline_entry_list = check.list_elem(pipelines_config, 'pipelines')

    for entry in pipeline_entry_list:
        pipeline_module_str = check.str_elem(entry, 'module')
        pipeline_fn_str = check.str_elem(entry, 'fn')

        pipeline_module = importlib.import_module(pipeline_module_str)
        pipeline_fn = getattr(pipeline_module, pipeline_fn_str)
        check.is_callable(pipeline_fn)

        pipeline = pipeline_fn()
        pipelines.append(pipeline)

    return pipelines


def dagster_cli_main(argv):
    check.list_param(argv, 'argv', of_type=str)

    dagster_command_group = click.Group(name='dagster')
    dagster_command_group.add_command(dagster_list_commmand)
    dagster_command_group(argv[1:])
