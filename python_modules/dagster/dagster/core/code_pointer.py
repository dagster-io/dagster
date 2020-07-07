import importlib
import inspect
import os
import sys
import warnings
from abc import ABCMeta, abstractmethod
from collections import namedtuple

import six

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError
from dagster.serdes import whitelist_for_serdes
from dagster.seven import import_module_from_path
from dagster.utils import alter_sys_path, load_yaml_from_path


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
    def from_python_package(module_name, attribute):
        check.str_param(module_name, 'module_name')
        check.str_param(attribute, 'attribute')
        return PackageCodePointer(module_name, attribute)

    @staticmethod
    def from_python_file(python_file, definition, working_directory):
        check.str_param(python_file, 'python_file')
        check.str_param(definition, 'definition')
        check.opt_str_param(working_directory, 'working_directory')
        if working_directory:
            return FileInDirectoryCodePointer(
                python_file=python_file, fn_name=definition, working_directory=working_directory
            )
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
            else CodePointer.from_python_file(rebase_file(file_name, file_path), fn_name, None)
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


def load_python_file(python_file, working_directory):
    '''
    Takes a path to a python file and returns a loaded module
    '''
    check.str_param(python_file, 'python_file')
    module_name = os.path.splitext(os.path.basename(python_file))[0]
    cwd = sys.path[0]
    if working_directory:
        with alter_sys_path(to_add=[working_directory], to_remove=[cwd]):
            return import_module_from_path(module_name, python_file)

    error = None
    sys_modules = {k: v for k, v in sys.modules.items()}

    with alter_sys_path(to_add=[], to_remove=[cwd]):
        try:
            module = import_module_from_path(module_name, python_file)
        except ImportError as ie:
            sys.modules = sys_modules
            error = ie

    if not error:
        return module

    try:
        module = import_module_from_path(module_name, python_file)
        # if here, we were able to resolve the module with the working directory on the
        # path, but should error because we may not always invoke from the same directory
        # (e.g. from cron)
        warnings.warn(
            (
                'Module `{module}` was resolved using the working directory. The ability to '
                'implicitly load modules from the working directory is deprecated and '
                'will be removed in a future release. Please explicitly specify the '
                '`working_directory` config option in your workspace.yaml or install `{module}` to '
                'your python environment.'
            ).format(module=error.name if hasattr(error, 'name') else module_name)
        )
        return module
    except ImportError:
        raise error


def load_python_module(module_name, warn_only=False, remove_from_path_fn=None):
    check.str_param(module_name, 'module_name')
    check.bool_param(warn_only, 'warn_only')
    check.opt_callable_param(remove_from_path_fn, 'remove_from_path_fn')

    error = None

    remove_paths = remove_from_path_fn() if remove_from_path_fn else []  # hook for tests
    remove_paths.insert(0, sys.path[0])  # remove the working directory

    with alter_sys_path(to_add=[], to_remove=remove_paths):
        try:
            module = importlib.import_module(module_name)
        except ImportError as ie:
            error = ie

    if error:
        try:
            module = importlib.import_module(module_name)

            # if here, we were able to resolve the module with the working directory on the path,
            # but should error because we may not always invoke from the same directory (e.g. from
            # cron)
            if warn_only:
                warnings.warn(
                    (
                        'Module {module} was resolved using the working directory. The ability to '
                        'load uninstalled modules from the working directory is deprecated and '
                        'will be removed in a future release.  Please use the python-file based '
                        'load arguments or install {module} to your python environment.'
                    ).format(module=module_name)
                )
            else:
                six.raise_from(
                    DagsterInvariantViolationError(
                        (
                            'Module {module} not found. Packages must be installed rather than '
                            'relying on the working directory to resolve module loading.'
                        ).format(module=module_name)
                    ),
                    error,
                )
        except ImportError as ie:
            raise error

    return module


@whitelist_for_serdes
class FileCodePointer(namedtuple('_FileCodePointer', 'python_file fn_name'), CodePointer):
    def __new__(cls, python_file, fn_name):
        return super(FileCodePointer, cls).__new__(
            cls, check.str_param(python_file, 'python_file'), check.str_param(fn_name, 'fn_name'),
        )

    def load_target(self):
        module = load_python_file(self.python_file, None)
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
class FileInDirectoryCodePointer(
    namedtuple('_FileInDirectoryCodePointer', 'python_file fn_name working_directory'), CodePointer
):
    '''
    Same as FileCodePointer, but with an additional field `working_directory` to help resolve
    modules that are resolved from the python invocation directory.  Required so other processes
    that need to resolve modules (e.g. cron scheduler) can do so.  This could be merged with the
    `FileCodePointer` with `working_directory` as a None-able field, but not without changing
    the origin_id for schedules.  This would require purging schedule storage to resolve.

    Should strongly consider merging when we need to do a storage migration.

    https://github.com/dagster-io/dagster/issues/2673
    '''

    def __new__(cls, python_file, fn_name, working_directory):
        return super(FileInDirectoryCodePointer, cls).__new__(
            cls,
            check.str_param(python_file, 'python_file'),
            check.str_param(fn_name, 'fn_name'),
            check.str_param(working_directory, 'working_directory'),
        )

    def load_target(self):
        module = load_python_file(self.python_file, self.working_directory)
        if not hasattr(module, self.fn_name):
            raise DagsterInvariantViolationError(
                '{name} not found at module scope in file {file}.'.format(
                    name=self.fn_name, file=self.python_file
                )
            )

        return getattr(module, self.fn_name)

    def describe(self):
        return '{self.python_file}::{self.fn_name} -- [dir {self.working_directory}]'.format(
            self=self
        )

    def get_cli_args(self):
        return '-f {python_file} -a {fn_name}  -d {directory}'.format(
            python_file=os.path.abspath(os.path.expanduser(self.python_file)),
            fn_name=self.fn_name,
            directory=self.working_directory,
        )


@whitelist_for_serdes
class ModuleCodePointer(namedtuple('_ModuleCodePointer', 'module fn_name'), CodePointer):
    def __new__(cls, module, fn_name):
        return super(ModuleCodePointer, cls).__new__(
            cls, check.str_param(module, 'module'), check.str_param(fn_name, 'fn_name')
        )

    def load_target(self):
        module = load_python_module(self.module, warn_only=True)

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


@whitelist_for_serdes
class PackageCodePointer(namedtuple('_PackageCodePointer', 'module attribute'), CodePointer):
    def __new__(cls, module, attribute):
        return super(PackageCodePointer, cls).__new__(
            cls, check.str_param(module, 'module'), check.str_param(attribute, 'attribute')
        )

    def load_target(self):
        module = load_python_module(self.module)

        if not hasattr(module, self.attribute):
            raise DagsterInvariantViolationError(
                '{name} not found in module {module}. dir: {dir}'.format(
                    name=self.attribute, module=self.module, dir=dir(module)
                )
            )
        return getattr(module, self.attribute)

    def describe(self):
        return 'from {self.module} import {self.attribute}'.format(self=self)

    def get_cli_args(self):
        return '-m {module} -a {attribute}'.format(module=self.module, attribute=self.attribute)


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
