import importlib
from collections import namedtuple
import logging
import textwrap
import os
import click
import yaml

from dagster import check
import dagster
from dagster.graphviz import build_graphviz_graph

from dagster import config as dagster_config
from dagster.core.errors import DagsterExecutionFailureReason
from dagster.core.execution import (
    DagsterExecutionContext,
    DagsterPipeline,
    execute_pipeline_iterator,
    materialize_pipeline_iterator,
    create_pipeline_env_from_arg_dicts,
)
from dagster.utils.logging import define_logger
from .embedded_cli import print_pipeline, process_results_for_console

LOGGING_DICT = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARN': logging.WARN,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}


class Config():
    def __init__(self, pipeline_configs):
        self.pipeline_configs = pipeline_configs
        self.pipelines = None

    @staticmethod
    def from_file(filepath):
        with open(filepath, 'r') as ff:
            config = yaml.load(ff)

        pipeline_configs = [
            PipelineConfig(module=check.str_elem(entry, 'module'), fn=check.str_elem(entry, 'fn'))
            for entry in check.list_elem(config, 'pipelines')
        ]

        return Config(pipeline_configs=pipeline_configs)

    def create_pipelines(self):
        for pipeline_config in self.pipeline_configs:
            pipeline_config.create_pipeline()

        return self.pipeline_configs

    def get_pipeline(self, name):
        if not self.pipelines:
            self.create_pipelines()

        for pipeline_config in self.pipeline_configs:
            if pipeline_config.pipeline.name == name:
                return pipeline_config

        check.failed(f'pipeline {name} not found')


pass_config = click.make_pass_decorator(Config)


class PipelineConfig():
    def __init__(self, module, fn):
        self.module_name = module
        self.fn_name = fn
        self.module = None
        self.fn = None
        self.pipeline = None

    def create_pipeline(self):
        self.module = importlib.import_module(self.module_name)
        self.fn = getattr(self.module, self.fn_name)
        check.is_callable(self.fn)
        self.pipeline = self.fn()
        return self.pipeline


@click.option(
    '--config',
    '-c',
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
    default='pipelines.yml',
    help="Path to config file. Defaults to ./pipelines.yml."
)
@click.pass_context
def dagster_cli(ctx, config):
    ctx.obj = Config.from_file(config)


def format_description(desc):
    dedented = textwrap.dedent(desc)
    indent = ' ' * 4
    wrapper = textwrap.TextWrapper(initial_indent=indent, subsequent_indent=indent)
    return wrapper.fill(dedented)


@click.command(name='list', help="list all pipelines")
@pass_config
def list_command(config):
    pipeline_configs = config.create_pipelines()

    for pipeline_config in pipeline_configs:
        pipeline = pipeline_config.pipeline
        click.echo('Pipeline: {name}'.format(name=pipeline.name))
        if pipeline.description:
            click.echo('Description:')
            click.echo(format_description(pipeline.description))
        click.echo('Solids: (Execution Order)')
        for solid in pipeline.solid_graph.topological_solids:
            click.echo('    ' + solid.name)
        click.echo('*************')


def set_pipeline(ctx, arg, value):
    ctx.params['pipeline_config'] = ctx.find_object(Config).get_pipeline(value)


def pipeline_name_argument(f):
    return click.argument('pipeline_name', callback=set_pipeline, expose_value=False)(f)


@click.command(name='print', help="[PIPELINE_NAME] print pipeline info")
@pipeline_name_argument
def print_command(pipeline_config):
    print_pipeline(pipeline_config.pipeline, full=True)


@click.command(name='graphviz', help="[PIPELINE_NAME] visualize pipeline")
@pipeline_name_argument
def graphviz_command(pipeline_config):
    build_graphviz_graph(pipeline_config.pipeline).view(cleanup=True)


def get_default_config_for_pipeline():
    ctx = click.get_current_context()
    pipeline_config = ctx.params['pipeline_config']
    module_path = os.path.dirname(pipeline_config.module.__file__)
    return os.path.join(module_path, 'env.yml')


@click.command(name='execute', help="[PIPELINE_NAME] execute pipeline")
@pipeline_name_argument
@click.option(
    '-e',
    '--env',
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
    default=get_default_config_for_pipeline,
    help="Path to environment file. Defaults to ./PIPELINE_DIR/env.yml."
)
@click.option('--from-solid', type=click.STRING, help="Solid to start execution from", default=None)
@click.option('--log-level', type=click.STRING, default='INFO')
def execute_command(pipeline_config, env, from_solid, log_level):
    with open(env, 'r') as ff:
        env_config = yaml.load(ff)
    environment = dagster_config.Environment(
        input_sources=[
            dagster_config.Input(input_name=s['input_name'], args=s['args'], source=s['source'])
            for s in check.list_elem(env_config['environment'], 'inputs')
        ]
    )

    materializations = []
    if 'materializations' in env_config:
        materializations = [
            dagster_config.Materialization(
                solid=m['solid'], materialization_type=m['type'], args=m['args']
            ) for m in check.list_elem(env_config, 'materializations')
        ]

    context = DagsterExecutionContext(loggers=[define_logger('dagster')], log_level=log_level)

    pipeline_iter = materialize_pipeline_iterator(
        context,
        pipeline_config.pipeline,
        environment=environment,
        materializations=materializations,
        from_solids=[from_solid] if from_solid else None,
        use_materialization_through_solids=False,
    )

    process_results_for_console(pipeline_iter, context)


def create_pipeline_cli():
    group = click.Group(name="pipeline")
    group.add_command(list_command)
    group.add_command(print_command)
    group.add_command(graphviz_command)
    group.add_command(execute_command)
    return group


def create_dagster_cli():
    group = click.group()(dagster_cli)
    group.add_command(create_pipeline_cli())
    return group
