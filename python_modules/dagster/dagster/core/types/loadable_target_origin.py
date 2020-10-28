from collections import namedtuple

from dagster import check


class LoadableTargetOrigin(
    namedtuple(
        "LoadableTargetOrigin",
        "executable_path python_file module_name working_directory attribute package_name",
    )
):
    def __new__(
        cls,
        executable_path,
        python_file=None,
        module_name=None,
        working_directory=None,
        attribute=None,
        package_name=None,
    ):
        return super(LoadableTargetOrigin, cls).__new__(
            cls,
            executable_path=check.str_param(executable_path, "executable_path"),
            python_file=check.opt_str_param(python_file, "python_file"),
            module_name=check.opt_str_param(module_name, "module_name"),
            working_directory=check.opt_str_param(working_directory, "working_directory"),
            attribute=check.opt_str_param(attribute, "attribute"),
            package_name=check.opt_str_param(package_name, "package_name"),
        )
