from collections import namedtuple

from dagster import check


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
