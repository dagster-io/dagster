from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, NamedTuple, Optional, Sequence

import dagster._check as check
from dagster._core.errors import DagsterInvariantViolationError
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
        executable_path: Optional[str] = None,
        python_file: Optional[str] = None,
        module_name: Optional[str] = None,
        working_directory: Optional[str] = None,
        attribute: Optional[str] = None,
        package_name: Optional[str] = None,
    ):
        return super(LoadableTargetOrigin, cls).__new__(
            cls,
            executable_path=check.opt_str_param(executable_path, "executable_path"),
            python_file=check.opt_str_param(python_file, "python_file"),
            module_name=check.opt_str_param(module_name, "module_name"),
            working_directory=check.opt_str_param(
                working_directory, "working_directory"
            ),
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

    @staticmethod
    def get() -> "LoadableTargetOrigin":
        ctx = _current_loadable_target_origin.get(None)
        if ctx is None:
            raise DagsterInvariantViolationError(
                "No LoadableTargetOrigin is currently being loaded."
            )
        return ctx

    @property
    def as_dict(self) -> dict:
        return {k: v for k, v in self._asdict().items() if v is not None}


_current_loadable_target_origin: ContextVar[Optional[LoadableTargetOrigin]] = (
    ContextVar("_current_loadable_target_origin", default=None)
)


@contextmanager
def enter_loadable_target_origin_load_context(
    loadable_target_origin: LoadableTargetOrigin,
) -> Iterator[None]:
    token = _current_loadable_target_origin.set(loadable_target_origin)
    try:
        yield
    finally:
        _current_loadable_target_origin.reset(token)
