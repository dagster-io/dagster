import importlib
import inspect
import os
import sys
from abc import ABCMeta, abstractmethod
from collections import namedtuple

import six

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError
from dagster.serdes import whitelist_for_serdes
from dagster.seven import import_module_from_path
from dagster.utils import load_yaml_from_path


class CodePointer(six.with_metaclass(ABCMeta)):
    @abstractmethod
    def load_target(self):
        pass

    @abstractmethod
    def describe(self):
        pass

    @staticmethod
    def from_module(module_name, definition):
        check.str_param(module_name, 'module_name')
        check.str_param(definition, 'definition')
        return ModuleCodePointer(module_name, definition)

    @staticmethod
    def from_python_file(python_file, definition):
        check.str_param(python_file, 'python_file')
        check.str_param(definition, 'definition')
        return FileCodePointer(python_file=python_file, fn_name=definition)

    @staticmethod
    def from_legacy_repository_yaml(file_path):
        check.str_param(file_path, 'file_path')
        config = load_yaml_from_path(file_path)
        repository_config = check.dict_elem(config, 'repository')
        module_name = check.opt_str_elem(repository_config, 'module')
        file_name = check.opt_str_elem(repository_config, 'file')
        fn_name = check.str_elem(repository_config, 'fn')

        return (
            CodePointer.from_module(module_name, fn_name)
            if module_name
            # rebase file in config off of the path in the config file
            else CodePointer.from_python_file(rebase_file(file_name, file_path), fn_name)
        )


def rebase_file(relative_path_in_file, file_path_resides_in):
    '''
    In config files, you often put file paths that are meant to be relative
    to the location of that config file. This does that calculation.
    '''
    check.str_param(relative_path_in_file, 'relative_path_in_file')
    check.str_param(file_path_resides_in, 'file_path_resides_in')
    return os.path.join(
        os.path.dirname(os.path.abspath(file_path_resides_in)), relative_path_in_file
    )


def load_python_file(python_file):
    '''
    Takes a path to a python file and returns a loaded module
    '''
    check.str_param(python_file, 'python_file')
    module_name = os.path.splitext(os.path.basename(python_file))[0]
    return import_module_from_path(module_name, python_file)


@whitelist_for_serdes
class FileCodePointer(namedtuple('_FileCodePointer', 'python_file fn_name'), CodePointer):
    def __new__(cls, python_file, fn_name):
        return super(FileCodePointer, cls).__new__(
            cls, check.str_param(python_file, 'python_file'), check.str_param(fn_name, 'fn_name'),
        )

    def load_target(self):
        module = load_python_file(self.python_file)
        if not hasattr(module, self.fn_name):
            raise DagsterInvariantViolationError(
                '{name} not found at module scope in file {file}.'.format(
                    name=self.fn_name, file=self.python_file
                )
            )

        return getattr(module, self.fn_name)

    def describe(self):
        return '{self.python_file}::{self.fn_name}'.format(self=self)

    def get_cli_args(self):
        return '-f {python_file} -a {fn_name}'.format(
            python_file=os.path.abspath(os.path.expanduser(self.python_file)), fn_name=self.fn_name
        )


@whitelist_for_serdes
class ModuleCodePointer(namedtuple('_ModuleCodePointer', 'module fn_name'), CodePointer):
    def __new__(cls, module, fn_name):
        return super(ModuleCodePointer, cls).__new__(
            cls, check.str_param(module, 'module'), check.str_param(fn_name, 'fn_name')
        )

    def load_target(self):
        module = importlib.import_module(self.module)
        if not hasattr(module, self.fn_name):
            raise DagsterInvariantViolationError(
                '{name} not found in module {module}. dir: {dir}'.format(
                    name=self.fn_name, module=self.module, dir=dir(module)
                )
            )

        return getattr(module, self.fn_name)

    def describe(self):
        return 'from {self.module} import {self.fn_name}'.format(self=self)

    def get_cli_args(self):
        return '-m {module} -a {fn_name}'.format(module=self.module, fn_name=self.fn_name)


def get_python_file_from_previous_stack_frame():
    '''inspect.stack() lets us introspect the call stack; inspect.stack()[1] is the previous
    stack frame.

    In Python < 3.5, this is just a tuple, of which the python file of the previous frame is the 1st
    element.

    In Python 3.5+, this is a FrameInfo namedtuple instance; the python file of the previous frame
    remains the 1st element.
    '''

    # Since this is now a function in this file, we need to go back two hops to find the
    # callsite file.
    previous_stack_frame = inspect.stack(0)[2]

    # See: https://docs.python.org/3/library/inspect.html
    if sys.version_info.major == 3 and sys.version_info.minor >= 5:
        check.inst(previous_stack_frame, inspect.FrameInfo)
    else:
        check.inst(previous_stack_frame, tuple)

    python_file = previous_stack_frame[1]
    return os.path.abspath(python_file)
