from contextlib import contextmanager
from typing import Iterator, Optional

from .._protocol import (
    DAGSTER_EXTERNALS_ENV_KEYS,
    ExternalExecutionContextData,
    ExternalExecutionParams,
)
from .._util import DagsterExternalsError
from .base import ExternalExecutionContextLoader


class ExternalExecutionEnvContextLoader(ExternalExecutionContextLoader):
    _data: Optional[ExternalExecutionContextData] = None

    @contextmanager
    def setup(self, params: ExternalExecutionParams) -> Iterator[None]:
        self._validate_params(params)
        self._data = params["data"]
        yield

    def _validate_params(self, params: ExternalExecutionParams) -> None:
        try:
            assert isinstance(params.get("data"), dict)
        except AssertionError:
            raise DagsterExternalsError(
                f"`{self.__class__.__name__}` requires a `data` key in the"
                f" {DAGSTER_EXTERNALS_ENV_KEYS['context']} environment variable."
            )

    def load_context(self) -> ExternalExecutionContextData:
        assert self._data is not None
        return self._data
