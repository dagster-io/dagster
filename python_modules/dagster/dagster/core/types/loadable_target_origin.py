from collections import namedtuple

from dagster import check
from dagster.serdes import whitelist_for_serdes


@whitelist_for_serdes
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

    def get_cli_args(self):

        # Need to ensure that everything that consumes this knows about
        # --empty-working-directory and --use-python-package
        args = (
            (
                (
                    [
                        "-f",
                        self.python_file,
                    ]
                    + (
                        ["-d", self.working_directory]
                        if self.working_directory
                        else ["--empty-working-directory"]
                    )
                )
                if self.python_file
                else []
            )
            + (["-m", self.module_name] if self.module_name else [])
            + (["-a", self.attribute] if self.attribute else [])
            + (["--package-name", self.package_name] if self.package_name else [])
        )

        return args

    def get_root_path(self) -> str:
        if self.working_directory and self.python_file:
            return os.path.join(self.working_directory, self.python_file)
        elif self.python_file:
            return self.python_file
        # origin is a guaranteed string for non-namespace-packages
        elif self.module_name:
            spec = importlib.util.find_spec(self.module_name)
            assert spec is not None, f"Could not find module {self.module_name}."
            return cast(str, spec.origin)
        elif self.package_name:
            spec = importlib.util.find_spec(self.package_name)
            assert spec is not None, f"Could not find package {self.package_name}."
            assert spec.origin is not None, f"Namespace package has no root path."
            return os.path.dirname(spec.origin)
        else:
            raise Exception("Cannot resolve root path for LoadableTargetOrigin")
