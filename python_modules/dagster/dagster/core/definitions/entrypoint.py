import imp
import importlib
import os

from collections import namedtuple

from dagster import check
from .pipeline import PipelineDefinition
from .repository import RepositoryDefinition
from dagster.core.errors import DagsterInvariantViolationError
from dagster.utils import load_yaml_from_path


class LoaderEntrypoint(namedtuple('_LoaderEntrypoint', 'module module_name fn_name')):
    def __new__(cls, module, module_name, fn_name):
        return super(LoaderEntrypoint, cls).__new__(cls, module, module_name, fn_name)

    def perform_load(self):
        # in the decorator case the attribute will be the actual definition
        if not hasattr(self.module, self.fn_name):
            raise DagsterInvariantViolationError(
                '{name} not found in module {module}.'.format(name=self.fn_name, module=self.module)
            )

        fn_repo_or_pipeline = getattr(self.module, self.fn_name)
        if isinstance(fn_repo_or_pipeline, RepositoryDefinition) or isinstance(
            fn_repo_or_pipeline, PipelineDefinition
        ):
            return fn_repo_or_pipeline
        elif callable(fn_repo_or_pipeline):
            repo_or_pipeline = fn_repo_or_pipeline()

            if isinstance(repo_or_pipeline, (RepositoryDefinition, PipelineDefinition)):
                return repo_or_pipeline

            raise DagsterInvariantViolationError(
                '{fn_name} is a function but must return a PipelineDefinition '
                'or a RepositoryDefinition, or be decorated with @pipeline.'.format(
                    fn_name=self.fn_name
                )
            )
        else:
            raise DagsterInvariantViolationError(
                '{fn_name} must be a function that returns a PipelineDefinition '
                'or a RepositoryDefinition, or a function decorated with @pipeline.'.format(
                    fn_name=self.fn_name
                )
            )

    @staticmethod
    def from_file_target(python_file, fn_name):
        module_name = os.path.splitext(os.path.basename(python_file))[0]
        module = imp.load_source(module_name, python_file)
        return LoaderEntrypoint(module, module_name, fn_name)

    @staticmethod
    def from_module_target(module_name, fn_name):
        module = importlib.import_module(module_name)
        return LoaderEntrypoint(module, module_name, fn_name)

    @staticmethod
    def from_yaml(file_path):
        check.str_param(file_path, 'file_path')

        config = load_yaml_from_path(file_path)
        repository_config = check.dict_elem(config, 'repository')
        module_name = check.opt_str_elem(repository_config, 'module')
        file_name = check.opt_str_elem(repository_config, 'file')
        fn_name = check.str_elem(repository_config, 'fn')

        if module_name:
            return LoaderEntrypoint.from_module_target(module_name, fn_name)
        else:
            # rebase file in config off of the path in the config file
            file_name = os.path.join(os.path.dirname(os.path.abspath(file_path)), file_name)
            return LoaderEntrypoint.from_file_target(file_name, fn_name)
