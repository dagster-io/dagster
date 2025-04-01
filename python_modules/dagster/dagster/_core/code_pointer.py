import importlib
import inspect
import os
import sys
from abc import ABC, abstractmethod
from collections.abc import Sequence
from types import ModuleType
from typing import Callable, NamedTuple, Optional, cast

from dagster_shared.seven import get_import_error_message, import_module_from_path
from dagster_shared.utils.hash import hash_collection

import dagster._check as check
from dagster._core.errors import DagsterImportError, DagsterInvariantViolationError
from dagster._serdes import whitelist_for_serdes
from dagster._utils import alter_sys_path


class CodePointer(ABC):
    @abstractmethod
    def load_target(self) -> object:
        pass

    @abstractmethod
    def describe(self) -> str:
        pass

    @staticmethod
    def from_module(
        module_name: str, definition: str, working_directory: Optional[str]
    ) -> "ModuleCodePointer":
        check.str_param(module_name, "module_name")
        check.str_param(definition, "definition")
        check.opt_str_param(working_directory, "working_directory")
        return ModuleCodePointer(module_name, definition, working_directory)

    @staticmethod
    def from_python_package(
        module_name: str, attribute: str, working_directory: Optional[str]
    ) -> "PackageCodePointer":
        check.str_param(module_name, "module_name")
        check.str_param(attribute, "attribute")
        check.opt_str_param(working_directory, "working_directory")
        return PackageCodePointer(module_name, attribute, working_directory)

    @staticmethod
    def from_python_file(
        python_file: str, definition: str, working_directory: Optional[str]
    ) -> "FileCodePointer":
        check.str_param(python_file, "python_file")
        check.str_param(definition, "definition")
        check.opt_str_param(working_directory, "working_directory")
        return FileCodePointer(
            python_file=python_file, fn_name=definition, working_directory=working_directory
        )


def rebase_file(relative_path_in_file: str, file_path_resides_in: str) -> str:
    """In config files, you often put file paths that are meant to be relative
    to the location of that config file. This does that calculation.
    """
    check.str_param(relative_path_in_file, "relative_path_in_file")
    check.str_param(file_path_resides_in, "file_path_resides_in")
    return os.path.join(
        os.path.dirname(os.path.abspath(file_path_resides_in)), relative_path_in_file
    )


def load_python_file(python_file: str, working_directory: Optional[str]) -> ModuleType:
    """Takes a path to a python file and returns a loaded module."""
    check.str_param(python_file, "python_file")
    check.opt_str_param(working_directory, "working_directory")

    # First verify that the file exists
    os.stat(python_file)

    module_name = os.path.splitext(os.path.basename(python_file))[0]

    # Use the passed in working directory for local imports (sys.path[0] isn't
    # consistently set in the different entry points that Dagster uses to import code)
    script_path = sys.path[0]
    try:
        with alter_sys_path(
            to_add=([working_directory] if working_directory else []), to_remove=[script_path]
        ):
            return import_module_from_path(module_name, python_file)
    except ImportError as ie:
        python_file = os.path.abspath(os.path.expanduser(python_file))

        msg = get_import_error_message(ie)
        if msg == "attempted relative import with no known parent package":
            raise DagsterImportError(
                f"Encountered ImportError: `{msg}` while importing module {module_name} from "
                f"file {python_file}. Consider using the module-based options `-m` for "
                "CLI-based targets or the `python_module` workspace target."
            ) from ie

        if working_directory:
            abs_working_directory = os.path.abspath(os.path.expanduser(working_directory))
            raise DagsterImportError(
                f"Encountered ImportError: `{msg}` while importing module {module_name} from "
                f"file {python_file}. Local modules were resolved using the working "
                f"directory `{abs_working_directory}`. If another working directory should be "
                "used, please explicitly specify the appropriate path using the `-d` or "
                "`--working-directory` for CLI based targets or the `working_directory` "
                "configuration option for `python_file`-based workspace targets. "
            ) from ie
        else:
            raise DagsterImportError(
                f"Encountered ImportError: `{msg}` while importing module {module_name} from file"
                f" {python_file}. If relying on the working directory to resolve modules, please "
                "explicitly specify the appropriate path using the `-d` or "
                "`--working-directory` for CLI based targets or the `working_directory` "
                "configuration option for `python_file`-based workspace targets. "
            ) from ie


def load_python_module(
    module_name: str,
    working_directory: Optional[str],
    remove_from_path_fn: Optional[Callable[[], Sequence[str]]] = None,
) -> ModuleType:
    check.str_param(module_name, "module_name")
    check.opt_str_param(working_directory, "working_directory")
    check.opt_callable_param(remove_from_path_fn, "remove_from_path_fn")

    # Use the passed in working directory for local imports (sys.path[0] isn't
    # consistently set in the different entry points that Dagster uses to import code)
    remove_paths: list[str] = (
        list(remove_from_path_fn()) if remove_from_path_fn else []
    )  # hook for tests
    remove_paths.insert(0, sys.path[0])  # remove the script path
    with alter_sys_path(
        to_add=([working_directory] if working_directory else []), to_remove=remove_paths
    ):
        try:
            return importlib.import_module(module_name)
        except ImportError as ie:
            msg = get_import_error_message(ie)
            if working_directory:
                abs_working_directory = os.path.abspath(os.path.expanduser(working_directory))
                raise DagsterImportError(
                    f"Encountered ImportError: `{msg}` while importing module {module_name}. "
                    "Local modules were resolved using the working "
                    f"directory `{abs_working_directory}`. If another working directory should be "
                    "used, please explicitly specify the appropriate path using the `-d` or "
                    "`--working-directory` for CLI based targets or the `working_directory` "
                    "configuration option for workspace targets. "
                ) from ie
            else:
                raise DagsterImportError(
                    f"Encountered ImportError: `{msg}` while importing module {module_name}. "
                    "If relying on the working directory to resolve modules, please "
                    "explicitly specify the appropriate path using the `-d` or "
                    "`--working-directory` for CLI based targets or the `working_directory` "
                    "configuration option for workspace targets. "
                ) from ie


@whitelist_for_serdes
class FileCodePointer(
    NamedTuple(
        "_FileCodePointer",
        [("python_file", str), ("fn_name", str), ("working_directory", Optional[str])],
    ),
    CodePointer,
):
    def __new__(cls, python_file: str, fn_name: str, working_directory: Optional[str] = None):
        return super().__new__(
            cls,
            check.str_param(python_file, "python_file"),
            check.str_param(fn_name, "fn_name"),
            check.opt_str_param(working_directory, "working_directory"),
        )

    def load_target(self) -> object:
        module = load_python_file(self.python_file, self.working_directory)
        return _load_target_from_module(
            module, self.fn_name, f"at module scope in file {self.python_file}."
        )

    def describe(self) -> str:
        if self.working_directory:
            return f"{self.python_file}::{self.fn_name} -- [dir {self.working_directory}]"
        else:
            return f"{self.python_file}::{self.fn_name}"


def _load_target_from_module(module: ModuleType, fn_name: str, error_suffix: str) -> object:
    from dagster._core.definitions.module_loaders.load_assets_from_modules import (
        load_assets_from_modules,
    )
    from dagster._core.workspace.autodiscovery import LOAD_ALL_ASSETS

    if fn_name == LOAD_ALL_ASSETS:
        # LOAD_ALL_ASSETS is a special symbol that's returned when, instead of loading a particular
        # attribute, we should load all the assets in the module.
        return load_assets_from_modules([module])
    else:
        if not hasattr(module, fn_name):
            raise DagsterInvariantViolationError(f"{fn_name} not found {error_suffix}")

        return getattr(module, fn_name)


@whitelist_for_serdes
class ModuleCodePointer(
    NamedTuple(
        "_ModuleCodePointer",
        [("module", str), ("fn_name", str), ("working_directory", Optional[str])],
    ),
    CodePointer,
):
    def __new__(cls, module: str, fn_name: str, working_directory: Optional[str] = None):
        return super().__new__(
            cls,
            check.str_param(module, "module"),
            check.str_param(fn_name, "fn_name"),
            check.opt_str_param(working_directory, "working_directory"),
        )

    def load_target(self) -> object:
        module = load_python_module(self.module, self.working_directory)
        return _load_target_from_module(
            module, self.fn_name, f"in module {self.module}. dir: {dir(module)}"
        )

    def describe(self) -> str:
        return f"from {self.module} import {self.fn_name}"


@whitelist_for_serdes
class PackageCodePointer(
    NamedTuple(
        "_PackageCodePointer",
        [("module", str), ("attribute", str), ("working_directory", Optional[str])],
    ),
    CodePointer,
):
    def __new__(cls, module: str, attribute: str, working_directory: Optional[str] = None):
        return super().__new__(
            cls,
            check.str_param(module, "module"),
            check.str_param(attribute, "attribute"),
            check.opt_str_param(working_directory, "working_directory"),
        )

    def load_target(self) -> object:
        module = load_python_module(self.module, self.working_directory)
        return _load_target_from_module(
            module, self.attribute, f"in module {self.module}. dir: {dir(module)}"
        )

    def describe(self) -> str:
        return f"from {self.module} import {self.attribute}"


def get_python_file_from_target(target: object) -> Optional[str]:
    module = inspect.getmodule(target)
    python_file = getattr(module, "__file__", None)

    if not python_file:
        return None

    return os.path.abspath(python_file)


@whitelist_for_serdes
class CustomPointer(
    NamedTuple(
        "_CustomPointer",
        [
            ("reconstructor_pointer", ModuleCodePointer),
            ("reconstructable_args", Sequence[object]),
            ("reconstructable_kwargs", Sequence[Sequence]),
        ],
    ),
    CodePointer,
):
    def __new__(
        cls,
        reconstructor_pointer: ModuleCodePointer,
        reconstructable_args: Sequence[object],
        reconstructable_kwargs: Sequence[Sequence],
    ):
        check.inst_param(reconstructor_pointer, "reconstructor_pointer", ModuleCodePointer)
        # These are lists rather than tuples to circumvent the tuple serdes machinery -- since these
        # are user-provided, they aren't whitelisted for serdes.
        check.sequence_param(reconstructable_args, "reconstructable_args")
        check.sequence_param(reconstructable_kwargs, "reconstructable_kwargs")
        for reconstructable_kwarg in reconstructable_kwargs:
            check.list_param(reconstructable_kwarg, "reconstructable_kwarg")
            check.invariant(isinstance(reconstructable_kwarg[0], str), "Bad kwarg key")
            check.invariant(
                len(reconstructable_kwarg) == 2,
                f"Bad kwarg of length {len(reconstructable_kwarg)}, should be 2",
            )

        return super().__new__(
            cls,
            reconstructor_pointer,
            reconstructable_args,
            reconstructable_kwargs,
        )

    def load_target(self) -> object:
        reconstructor = cast(Callable, self.reconstructor_pointer.load_target())

        return reconstructor(
            *self.reconstructable_args, **{key: value for key, value in self.reconstructable_kwargs}
        )

    def describe(self) -> str:
        return f"reconstructable using {self.reconstructor_pointer.module}.{self.reconstructor_pointer.fn_name}"

    # Allow this to be hashed for use in `lru_cache`. This is needed because:
    # - `ReconstructableJob` uses `lru_cache`
    # - `ReconstructableJob` has a `ReconstructableRepository` attribute
    # - `ReconstructableRepository` has a `CodePointer` attribute
    # - `CustomCodePointer` has collection attributes that are unhashable by default
    def __hash__(self) -> int:
        if not hasattr(self, "_hash"):
            self._hash = hash_collection(self)
        return self._hash
