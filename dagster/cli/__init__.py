import importlib
from collections import namedtuple
import logging

import click
import yaml

from dagster import check
from dagster.graphviz import build_graphviz_graph
from dagster import config
from dagster.core.errors import DagsterExecutionFailureReason
from dagster.core.execution import (
    DagsterExecutionContext,
    DagsterPipeline,
    execute_pipeline_iterator,
    materialize_pipeline_iterator,
    create_pipeline_env_from_arg_dicts,
)
from dagster.utils.logging import define_logger
from .embedded_cli import print_pipeline, construct_arg_dicts, _get_materializations, process_results_for_console

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
        self.pipelines = []

        for pipeline_config in self.pipeline_configs:
            pipeline = pipeline_config.create_pipeline()
            self.pipelines.append(pipeline)

        return self.pipelines

    def get_pipeline(self, name):
        if not self.pipelines:
            self.create_pipelines()

        for pipeline in self.pipelines:
            if pipeline.name == name:
                return pipeline

        check.failed(f'pipeline {name} not found')


pass_config = click.make_pass_decorator(Config)


class PipelineConfig():
    def __init__(self, module, fn):
        self.module = module
        self.fn = fn

    def create_pipeline(self):
        pipeline_module = importlib.import_module(self.module)
        pipeline_fn = getattr(pipeline_module, self.fn)
        check.is_callable(pipeline_fn)
        pipeline = pipeline_fn()
        return pipeline


pass_pipeline = click.make_pass_decorator(DagsterPipeline)


@click.group()
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


@dagster_cli.command(name='list', help="list all pipelines")
@pass_config
def dagster_list_commmand(config):
    pipelines = config.create_pipelines()

    for pipeline in pipelines:
        click.echo('Pipeline: {name}'.format(name=pipeline.name))


# XXX(freiksenet): Might not be a good idea UI wise
@dagster_cli.group(help="PIPELINE_NAME operate on pipeline")
@click.argument('pipeline_name')
@click.pass_context
def pipeline(ctx, pipeline_name):
    pipeline = ctx.obj.get_pipeline(pipeline_name)
    ctx.obj = pipeline


@pipeline.command(name='print')
@pass_pipeline
def dagster_print_commmand(pipeline):
    print_pipeline(pipeline, full=True)


@pipeline.command(name='graphviz')
@pass_pipeline
def dagster_graphviz_commmand(pipeline, name):
    build_graphviz_graph(pipeline).view(cleanup=True)


@pipeline.command(name='execute')
@click.option('--input', multiple=True)
@click.option('--materialization', multiple=True)
@click.option('--through', multiple=True)
@click.option('--log-level', type=click.STRING, default='INFO')
@pass_pipeline
def execute(pipeline, input, through, materialization, log_level):
    check.opt_tuple_param(input, 'input')
    check.opt_tuple_param(materialization, 'materialization')
    check.opt_str_param(log_level, 'log_level')

    input_list = list(input)
    through_list = list(through)
    materialization_list = list(materialization)

    input_arg_dicts = construct_arg_dicts(input_list)
    materializations = _get_materializations(materialization_list)

    context = DagsterExecutionContext(loggers=[define_logger('dagster')], log_level=log_level)

    pipeline_iter = materialize_pipeline_iterator(
        context,
        pipeline,
        environment=create_pipeline_env_from_arg_dicts(pipeline, input_arg_dicts),
        materializations=materializations,
        # XXX(freiksenet): Need to figure this out, it's currently implied from
        # materializations, but does it mean only materialized solids get
        # executed? that's weird
        # through_solids=through_list
    )

    process_results_for_console(pipeline_iter, context)
