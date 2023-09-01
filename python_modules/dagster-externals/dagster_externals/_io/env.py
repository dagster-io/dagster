from contextlib import contextmanager
from typing import Iterator, cast

from .._protocol import (
    ExternalExecutionContextData,
    ExternalExecutionParams,
)
from .._util import assert_env_param_type
from .base import ExternalExecutionContextLoader


class ExternalExecutionEnvContextLoader(ExternalExecutionContextLoader):
    @contextmanager
    def load_context(
        self, params: ExternalExecutionParams
    ) -> Iterator["ExternalExecutionContextData"]:
        data = assert_env_param_type(params, "data", dict, self.__class__)
        yield cast(ExternalExecutionContextData, data)
