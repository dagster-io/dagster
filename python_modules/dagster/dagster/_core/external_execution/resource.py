import json
from abc import ABC, abstractmethod
from typing import Mapping, Optional

from dagster_externals import (
    DAGSTER_EXTERNALS_ENV_KEYS,
    ExternalExecutionExtras,
)

from dagster._config.pythonic_config import ConfigurableResource
from dagster._core.execution.context.compute import OpExecutionContext


class ExternalExecutionResource(ConfigurableResource, ABC):
    def get_base_env(self) -> Mapping[str, str]:
        return {DAGSTER_EXTERNALS_ENV_KEYS["is_orchestration_active"]: json.dumps(True)}

    @abstractmethod
    def run(
        self,
        *,
        context: OpExecutionContext,
        extras: Optional[ExternalExecutionExtras] = None,
    ) -> None:
        ...
