from contextlib import contextmanager
from typing import Iterator, cast

from .._protocol import (
    ExtContextData,
    ExtParams,
)
from .._util import assert_env_param_type
from .base import ExtContextLoader


class ExtEnvContextLoader(ExtContextLoader):
    @contextmanager
    def load_context(self, params: ExtParams) -> Iterator["ExtContextData"]:
        data = assert_env_param_type(params, "data", dict, self.__class__)
        yield cast(ExtContextData, data)
