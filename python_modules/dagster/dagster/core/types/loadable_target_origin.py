from collections import namedtuple

from dagster import check
from dagster.core.code_pointer import FileCodePointer, ModuleCodePointer, PackageCodePointer
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.origin import RepositoryPythonOrigin


class LoadableTargetOrigin(
    namedtuple(
        "LoadableTargetOrigin",
        "executable_path python_file module_name working_directory attribute",
    )
):
    def __new__(
        cls,
        executable_path=None,
        python_file=None,
        module_name=None,
        working_directory=None,
        attribute=None,
    ):
        return super(LoadableTargetOrigin, cls).__new__(
            cls,
            executable_path=check.opt_str_param(executable_path, "executable_path"),
            python_file=check.opt_str_param(python_file, "python_file"),
            module_name=check.opt_str_param(module_name, "module_name"),
            working_directory=check.opt_str_param(working_directory, "working_directory"),
            attribute=check.opt_str_param(attribute, "attribute"),
        )

    @staticmethod
    def from_python_origin(repository_python_origin):
        check.inst_param(
            repository_python_origin, "repository_python_origin", RepositoryPythonOrigin
        )
        executable_path = repository_python_origin.executable_path
        code_pointer = repository_python_origin.code_pointer
        if isinstance(code_pointer, FileCodePointer):
            return LoadableTargetOrigin(
                executable_path=executable_path,
                python_file=code_pointer.python_file,
                attribute=code_pointer.fn_name,
                working_directory=code_pointer.working_directory,
            )
        elif isinstance(code_pointer, ModuleCodePointer):
            return LoadableTargetOrigin(
                executable_path=executable_path,
                module_name=code_pointer.module,
                attribute=code_pointer.fn_name,
            )
        elif isinstance(code_pointer, PackageCodePointer):
            return LoadableTargetOrigin(
                executable_path=executable_path,
                module_name=code_pointer.module,
                attribute=code_pointer.attribute,
            )
        else:
            raise DagsterInvariantViolationError(
                "Unexpected code pointer {code_pointer_name}".format(
                    code_pointer_name=type(code_pointer).__name__
                )
            )
