from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, Mapping, Optional

from dagster_ext import (
    DAGSTER_EXT_ENV_KEYS,
    ExtExtras,
    ExtParams,
    encode_env_var,
)

from dagster._config.pythonic_config import ConfigurableResource
from dagster._core.execution.context.compute import OpExecutionContext

if TYPE_CHECKING:
    from dagster._core.ext.context import ExtOrchestrationContext


class ExtResource(ConfigurableResource, ABC):
    def get_base_env(self) -> Mapping[str, str]:
        return {DAGSTER_EXT_ENV_KEYS["is_orchestration_active"]: encode_env_var(True)}

    @abstractmethod
    def run(
        self,
        *,
        context: OpExecutionContext,
        extras: Optional[ExtExtras] = None,
        context_injector: Optional["ExtContextInjector"] = None,
        message_reader: Optional["ExtMessageReader"] = None,
    ) -> None:
        ...


class ExtContextInjector(ABC):
    @abstractmethod
    @contextmanager
    def inject_context(self, context: "ExtOrchestrationContext") -> Iterator[ExtParams]:
        ...


class ExtMessageReader(ABC):
    @abstractmethod
    @contextmanager
    def read_messages(self, context: "ExtOrchestrationContext") -> Iterator[ExtParams]:
        ...
