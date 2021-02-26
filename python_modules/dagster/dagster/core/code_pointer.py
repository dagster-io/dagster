import importlib
import inspect
import os
import sys
import warnings
from abc import ABC, abstractmethod
from collections import namedtuple

from dagster import check
from dagster.core.errors import DagsterImportError, DagsterInvariantViolationError
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.serdes import whitelist_for_serdes
from dagster.seven import get_import_error_message, import_module_from_path
from dagster.utils import alter_sys_path, frozenlist, load_yaml_from_path


class CodePointer(ABC):
    @abstractmethod
    def load_target(self):
        pass

    @abstractmethod
    def describe(self):
        pass

    @abstractmethod
    def get_loadable_target_origin(self, executable_path):
        pass

    @staticmethod
    def from_module(module_name, definition):
        check.str_param(module_name, "module_name")
        check.str_param(definition, "definition")
        return ModuleCodePointer(module_name, definition)

    @staticmethod
    def from_python_package(module_name, attribute):
        check.str_param(module_name, "module_name")
        check.str_param(attribute, "attribute")
        return PackageCodePointer(module_name, attribute)

    @staticmethod
    def from_python_file(python_file, definition, working_directory):
        check.str_param(python_file, "python_file")
        check.str_param(definition, "definition")
        check.opt_str_param(working_directory, "working_directory")
        return FileCodePointer(
            python_file=python_file, fn_name=definition, working_directory=working_directory
        )

    @staticmethod
    def from_legacy_repository_yaml(file_path):
        check.str_param(file_path, "file_path")
        config = load_yaml_from_path(file_path)
        repository_config = check.dict_elem(config, "repository")
        module_name = check.opt_str_elem(repository_config, "module")
        file_name = check.opt_str_elem(repository_config, "file")
        fn_name = check.str_elem(repository_config, "fn")

        return (
            CodePointer.from_module(module_name, fn_name)
            if module_name
            # rebase file in config off of the path in the config file
            else CodePointer.from_python_file(rebase_file(file_name, file_path), fn_name, None)
        )


def rebase_file(relative_path_in_file, file_path_resides_in):
    """
    In config files, you often put file paths that are meant to be relative
    to the location of that config file. This does that calculation.
    """
    check.str_param(relative_path_in_file, "relative_path_in_file")
    check.str_param(file_path_resides_in, "file_path_resides_in")
    return os.path.join(
        os.path.dirname(os.path.abspath(file_path_resides_in)), relative_path_in_file
    )


def load_python_file(python_file, working_directory):
    """
    Takes a path to a python file and returns a loaded module
    """
    check.str_param(python_file, "python_file")

    # First verify that the file exists
    os.stat(python_file)

    module_name = os.path.splitext(os.path.basename(python_file))[0]
    cwd = sys.path[0]
    if working_directory:
        try:
            with alter_sys_path(to_add=[working_directory], to_remove=[cwd]):
                return import_module_from_path(module_name, python_file)
        except ImportError as ie:
            msg = get_import_error_message(ie)
            python_file = os.path.abspath(os.path.expanduser(python_file))

            if msg == "attempted relative import with no known parent package":

                raise DagsterImportError(
                    f"Encountered ImportError: `{msg}` while importing module {module_name} from "
                    f"file {python_file}. Consider using the module-based options `-m` for "
                    "CLI-based targets or the `python_package` workspace.yaml target."
                ) from ie

            working_directory = os.path.abspath(os.path.expanduser(working_directory))

            raise DagsterImportError(
                f"Encountered ImportError: `{msg}` while importing module {module_name} from "
                f"file {python_file}. Local modules were resolved using the working "
                f"directory `{working_directory}`. If another working directory should be "
                "used, please explicitly specify the appropriate path using the `-d` or "
                "`--working-directory` for CLI based targets or the `working_directory` "
                "configuration option for `python_file`-based workspace.yaml targets. "
            ) from ie

    error = None
    sys_modules = {k: v for k, v in sys.modules.items()}

    with alter_sys_path(to_add=[], to_remove=[cwd]):
        try:
            module = import_module_from_path(module_name, python_file)
        except ImportError as ie:
            # importing alters sys.modules in ways that may interfere with the import below, even
            # if the import has failed.  to work around this, we need to manually clear any modules
            # that have been cached in sys.modules due to the speculative import call
            # Also, we are mutating sys.modules instead of straight-up assigning to sys_modules,
            # because some packages will do similar shenanigans to sys.modules (e.g. numpy)
            to_delete = set(sys.modules) - set(sys_modules)
            for key in to_delete:
                del sys.modules[key]
            error = ie

    if not error:
        return module

    try:
        module = import_module_from_path(module_name, python_file)
        # if here, we were able to resolve the module with the working directory on the
        # path, but should warn because we may not always invoke from the same directory
        # (e.g. from cron)
        module_name = error.name if hasattr(error, "name") else module_name

        warnings.warn(
            f"Module `{module_name}` was resolved using the working directory. The ability to "
            "implicitly load modules from the working directory is deprecated and "
            "will be removed in a future release. Please explicitly specify the "
            "`working_directory` config option in your workspace.yaml or install "
            f"`{module_name}` to your python environment."
        )
        return module
    except RuntimeError:
        # We might be here because numpy throws run time errors at import time when being imported
        # multiple times... we should also use the original import error as the root
        python_file = os.path.abspath(os.path.expanduser(python_file))

        raise DagsterImportError(
            f"Encountered ImportError: `{error.msg}` while importing module {module_name} from file"
            f" {python_file}. If relying on the working directory to resolve modules, please "
            "explicitly specify the appropriate path using the `-d` or "
            "`--working-directory` for CLI based targets or the `working_directory` "
            "configuration option for `python_file`-based workspace.yaml targets. " + error.msg
        ) from error
    except ImportError:
        # raise the original import error
        raise error


def load_python_module(module_name, warn_only=False, remove_from_path_fn=None):
    check.str_param(module_name, "module_name")
    check.bool_param(warn_only, "warn_only")
    check.opt_callable_param(remove_from_path_fn, "remove_from_path_fn")

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
                    f"Module {module_name} was resolved using the working directory. The ability to"
                    " load uninstalled modules from the working directory is deprecated and "
                    "will be removed in a future release.  Please use the python-file based "
                    f"load arguments or install {module_name} to your python environment."
                )
            else:
                raise DagsterInvariantViolationError(
                    f"Module {module_name} not found. Packages must be installed rather than "
                    "relying on the working directory to resolve module loading."
                ) from error
        except RuntimeError:
            # We might be here because numpy throws run time errors at import time when being
            # imported multiple times, just raise the original import error
            raise error
        except ImportError as ie:
            raise error

    return module


@whitelist_for_serdes
class FileCodePointer(
    namedtuple("_FileCodePointer", "python_file fn_name working_directory"), CodePointer
):
    def __new__(cls, python_file, fn_name, working_directory=None):
        check.opt_str_param(working_directory, "working_directory")
        return super(FileCodePointer, cls).__new__(
            cls,
            check.str_param(python_file, "python_file"),
            check.str_param(fn_name, "fn_name"),
            working_directory,
        )

    def load_target(self):
        module = load_python_file(self.python_file, self.working_directory)
        if not hasattr(module, self.fn_name):
            raise DagsterInvariantViolationError(
                "{name} not found at module scope in file {file}.".format(
                    name=self.fn_name, file=self.python_file
                )
            )

        return getattr(module, self.fn_name)

    def describe(self):
        if self.working_directory:
            return "{self.python_file}::{self.fn_name} -- [dir {self.working_directory}]".format(
                self=self
            )
        else:
            return "{self.python_file}::{self.fn_name}".format(self=self)

    def get_cli_args(self):
        if self.working_directory:
            return "-f {python_file} -a {fn_name} -d {directory}".format(
                python_file=os.path.abspath(os.path.expanduser(self.python_file)),
                fn_name=self.fn_name,
                directory=os.path.abspath(os.path.expanduser(self.working_directory)),
            )
        else:
            return "-f {python_file} -a {fn_name}".format(
                python_file=os.path.abspath(os.path.expanduser(self.python_file)),
                fn_name=self.fn_name,
            )

    def get_loadable_target_origin(self, executable_path):
        return LoadableTargetOrigin(
            executable_path=executable_path,
            python_file=self.python_file,
            attribute=self.fn_name,
            working_directory=self.working_directory,
        )


@whitelist_for_serdes
class ModuleCodePointer(namedtuple("_ModuleCodePointer", "module fn_name"), CodePointer):
    def __new__(cls, module, fn_name):
        return super(ModuleCodePointer, cls).__new__(
            cls, check.str_param(module, "module"), check.str_param(fn_name, "fn_name")
        )

    def load_target(self):
        module = load_python_module(self.module, warn_only=True)

        if not hasattr(module, self.fn_name):
            raise DagsterInvariantViolationError(
                "{name} not found in module {module}. dir: {dir}".format(
                    name=self.fn_name, module=self.module, dir=dir(module)
                )
            )
        return getattr(module, self.fn_name)

    def describe(self):
        return "from {self.module} import {self.fn_name}".format(self=self)

    def get_cli_args(self):
        return "-m {module} -a {fn_name}".format(module=self.module, fn_name=self.fn_name)

    def get_loadable_target_origin(self, executable_path):
        return LoadableTargetOrigin(
            executable_path=executable_path,
            module_name=self.module,
            attribute=self.fn_name,
        )


@whitelist_for_serdes
class PackageCodePointer(namedtuple("_PackageCodePointer", "module attribute"), CodePointer):
    def __new__(cls, module, attribute):
        return super(PackageCodePointer, cls).__new__(
            cls, check.str_param(module, "module"), check.str_param(attribute, "attribute")
        )

    def load_target(self):
        module = load_python_module(self.module)

        if not hasattr(module, self.attribute):
            raise DagsterInvariantViolationError(
                "{name} not found in module {module}. dir: {dir}".format(
                    name=self.attribute, module=self.module, dir=dir(module)
                )
            )
        return getattr(module, self.attribute)

    def describe(self):
        return "from {self.module} import {self.attribute}".format(self=self)

    def get_cli_args(self):
        return "-m {module} -a {attribute}".format(module=self.module, attribute=self.attribute)

    def get_loadable_target_origin(self, executable_path):
        return LoadableTargetOrigin(
            executable_path=executable_path,
            module_name=self.module,
            attribute=self.attribute,
        )


def get_python_file_from_target(target):
    module = inspect.getmodule(target)
    python_file = getattr(module, "__file__", None)

    if not python_file:
        return None

    return os.path.abspath(python_file)


@whitelist_for_serdes
class CustomPointer(
    namedtuple(
        "_CustomPointer", "reconstructor_pointer reconstructable_args reconstructable_kwargs"
    ),
    CodePointer,
):
    def __new__(cls, reconstructor_pointer, reconstructable_args, reconstructable_kwargs):
        check.inst_param(reconstructor_pointer, "reconstructor_pointer", ModuleCodePointer)
        # These are lists rather than tuples to circumvent the tuple serdes machinery -- since these
        # are user-provided, they aren't whitelisted for serdes.
        check.list_param(reconstructable_args, "reconstructable_args")
        check.list_param(reconstructable_kwargs, "reconstructable_kwargs")
        for reconstructable_kwarg in reconstructable_kwargs:
            check.list_param(reconstructable_kwarg, "reconstructable_kwarg")
            check.invariant(isinstance(reconstructable_kwarg[0], str), "Bad kwarg key")
            check.invariant(
                len(reconstructable_kwarg) == 2,
                "Bad kwarg of length {length}, should be 2".format(
                    length=len(reconstructable_kwarg)
                ),
            )

        # These are frozenlists, rather than lists, so that they can be hashed and the pointer
        # stored in the lru_cache on the repository and pipeline get_definition methods
        reconstructable_args = frozenlist(reconstructable_args)
        reconstructable_kwargs = frozenlist(
            [frozenlist(reconstructable_kwarg) for reconstructable_kwarg in reconstructable_kwargs]
        )

        return super(CustomPointer, cls).__new__(
            cls,
            reconstructor_pointer,
            reconstructable_args,
            reconstructable_kwargs,
        )

    def load_target(self):
        reconstructor = self.reconstructor_pointer.load_target()

        return reconstructor(
            *self.reconstructable_args, **{key: value for key, value in self.reconstructable_kwargs}
        )

    def describe(self):
        return "reconstructable using {module}.{fn_name}".format(
            module=self.reconstructor_pointer.module, fn_name=self.reconstructor_pointer.fn_name
        )

    def get_loadable_target_origin(self, executable_path):
        raise NotImplementedError()
