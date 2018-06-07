import importlib

import click
import yaml

from dagster import check


def define_config_class():
    class _Config:
        def __init__(self, pipeline_configs):
            self.pipeline_configs = pipeline_configs
            self.pipelines = None

        @staticmethod
        def from_file(filepath):
            with open(filepath, 'r') as ff:
                config = yaml.load(ff)

            pipeline_configs = [
                PipelineConfig(
                    module=check.str_elem(entry, 'module'), fn=check.str_elem(entry, 'fn')
                ) for entry in check.list_elem(config, 'pipelines')
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

    _Config.pass_object = click.make_pass_decorator(_Config)
    return _Config


# This lets you ask cli commands to have this object extracted from context and
# passed as first arg

Config = define_config_class()


def define_pipeline_config():
    class _PipelineConfig:
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

    _PipelineConfig.pass_object = click.make_pass_decorator(_PipelineConfig)
    return _PipelineConfig


PipelineConfig = define_pipeline_config()
# This lets you ask cli commands to have this object extracted from context and
# passed as first arg
