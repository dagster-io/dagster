from typing import NamedTuple, Optional, Sequence

import dagster._check as check
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
class LoadableTargetOrigin(
    NamedTuple(
        "LoadableTargetOrigin",
        [
            ("executable_path", Optional[str]),
            ("python_file", Optional[str]),
            ("module_name", Optional[str]),
            ("working_directory", Optional[str]),
            ("attribute", Optional[str]),
            ("package_name", Optional[str]),
        ],
    )
):
    def __new__(
        cls,
        executable_path=None,
        python_file=None,
        module_name=None,
        working_directory=None,
        attribute=None,
        package_name=None,
    ):
        return super(LoadableTargetOrigin, cls).__new__(
            cls,
            executable_path=check.opt_str_param(executable_path, "executable_path"),
            python_file=check.opt_str_param(python_file, "python_file"),
            module_name=check.opt_str_param(module_name, "module_name"),
            working_directory=check.opt_str_param(working_directory, "working_directory"),
            attribute=check.opt_str_param(attribute, "attribute"),
            package_name=check.opt_str_param(package_name, "package_name"),
        )

    def get_cli_args(self) -> Sequence[str]:
        args = (
            (["-f", self.python_file] if self.python_file else [])
            + (["-m", self.module_name] if self.module_name else [])
            + (["-d", self.working_directory] if self.working_directory else [])
            + (["-a", self.attribute] if self.attribute else [])
            + (["--package-name", self.package_name] if self.package_name else [])
        )

        return args
