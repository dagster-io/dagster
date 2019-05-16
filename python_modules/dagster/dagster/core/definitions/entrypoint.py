import imp
import importlib
import os

from collections import namedtuple

from dagster import check
from dagster.utils import load_yaml_from_path


class LoaderEntrypoint(namedtuple('_LoaderEntrypoint', 'module module_name fn_name')):
    def __new__(cls, module, module_name, fn_name):
        return super(LoaderEntrypoint, cls).__new__(cls, module, module_name, fn_name)

    def perform_load(self):
        fn = getattr(self.module, self.fn_name)
        check.is_callable(fn)
        return fn()

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
