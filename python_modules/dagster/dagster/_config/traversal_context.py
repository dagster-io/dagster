from abc import ABC, abstractmethod
from enum import Enum
from typing_extensions import Self

import dagster._check as check

from .config_type import ConfigType
from .field import Field
from .snap import ConfigFieldSnap, ConfigSchemaSnap, ConfigTypeSnap
from .stack import EvaluationStack


class TraversalType(Enum):
    VALIDATE = "VALIDATE"
    RESOLVE_DEFAULTS = "RESOLVE_DEFAULTS"
    RESOLVE_DEFAULTS_AND_POSTPROCESS = "RESOLVE_DEFAULTS_AND_POSTPROCESS"


class TraversalContext(ABC):
    __slots__ = ["_config_schema_snapshot", "_config_type_snap", "_stack"]

    _config_schema_snapshot: ConfigSchemaSnap
    _config_type_snap: ConfigTypeSnap
    _stack: EvaluationStack

    def __init__(
        self,
        config_schema_snapshot: ConfigSchemaSnap,
        config_type_snap: ConfigTypeSnap,
        stack: EvaluationStack,
    ):
        self._config_schema_snapshot = check.inst_param(
            config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnap
        )

        self._config_type_snap = check.inst_param(
            config_type_snap, "config_type_snap", ConfigTypeSnap
        )

        self._stack = check.inst_param(stack, "stack", EvaluationStack)

    @property
    def config_schema_snapshot(self) -> ConfigSchemaSnap:
        return self._config_schema_snapshot

    @property
    def config_type_snap(self) -> ConfigTypeSnap:
        return self._config_type_snap

    @property
    def config_type_key(self) -> str:
        return self._config_type_snap.key

    @property
    def stack(self) -> EvaluationStack:
        return self._stack

    @abstractmethod
    def for_array_element(self: Self, index: int) -> Self:
        ...

    @abstractmethod
    def for_map_key(self: Self, index: int) -> Self:
        ...

    @abstractmethod
    def for_map_value(self: Self, map_key: object) -> Self:
        ...





