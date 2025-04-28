from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, Optional, Sequence

from dagster._core.errors import DagsterInvariantViolationError
from dagster._serdes import whitelist_for_serdes
from dagster_shared.record import NamedTupleAdapter, record, as_dict


@whitelist_for_serdes
@record
class LoadableTargetOrigin(NamedTupleAdapter["LoadableTargetOrigin"]):
    executable_path: Optional[str] = None
    python_file: Optional[str] = None
    module_name: Optional[str] = None
    working_directory: Optional[str] = None
    attribute: Optional[str] = None
    package_name: Optional[str] = None

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
        return {k: v for k, v in as_dict(self).items() if v is not None}


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
