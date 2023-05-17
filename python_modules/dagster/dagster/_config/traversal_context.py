from enum import Enum

import dagster._check as check

from .config_type import ConfigType
from .field import Field
from .snap import ConfigFieldSnap, ConfigSchemaSnapshot, ConfigTypeSnap
from .stack import EvaluationStack


class TraversalType(Enum):
    VALIDATE = "VALIDATE"
    RESOLVE_DEFAULTS = "RESOLVE_DEFAULTS"
    RESOLVE_DEFAULTS_AND_POSTPROCESS = "RESOLVE_DEFAULTS_AND_POSTPROCESS"


class ContextData:
    __slots__ = ["_config_schema_snapshot", "_config_type_snap", "_stack"]

    _config_schema_snapshot: ConfigSchemaSnapshot
    _config_type_snap: ConfigTypeSnap
    _stack: EvaluationStack

    def __init__(
        self,
        config_schema_snapshot: ConfigSchemaSnapshot,
        config_type_snap: ConfigTypeSnap,
        stack: EvaluationStack,
    ):
        self._config_schema_snapshot = check.inst_param(
            config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot
        )

        self._config_type_snap = check.inst_param(
            config_type_snap, "config_type_snap", ConfigTypeSnap
        )

        self._stack = check.inst_param(stack, "stack", EvaluationStack)

    @property
    def config_schema_snapshot(self) -> ConfigSchemaSnapshot:
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


class ValidationContext(ContextData):
    def for_field_snap(self, field_snap: ConfigFieldSnap) -> "ValidationContext":
        check.inst_param(field_snap, "field_snap", ConfigFieldSnap)
        field_snap_name = check.not_none(field_snap.name)
        return ValidationContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(field_snap.type_key),
            stack=self.stack.for_field(field_snap_name),
        )

    def for_array(self, index: int) -> "ValidationContext":
        check.int_param(index, "index")
        return ValidationContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(
                self.config_type_snap.inner_type_key
            ),
            stack=self.stack.for_array_index(index),
        )

    def for_map_key(self, key: object) -> "ValidationContext":
        return ValidationContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(
                self.config_type_snap.key_type_key
            ),
            stack=self.stack.for_map_key(key),
        )

    def for_map_value(self, key: object) -> "ValidationContext":
        return ValidationContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(
                self.config_type_snap.inner_type_key
            ),
            stack=self.stack.for_map_value(key),
        )

    def for_new_config_type_key(self, config_type_key: str) -> "ValidationContext":
        check.str_param(config_type_key, "config_type_key")
        return ValidationContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(config_type_key),
            stack=self.stack,
        )

    def for_nullable_inner_type(self) -> "ValidationContext":
        return ValidationContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(
                self.config_type_snap.inner_type_key
            ),
            stack=self.stack,
        )


class TraversalContext(ContextData):
    __slots__ = ["_config_type", "_traversal_type", "_all_config_types"]

    def __init__(
        self,
        config_schema_snapshot: ConfigSchemaSnapshot,
        config_type_snap: ConfigTypeSnap,
        config_type: ConfigType,
        stack: EvaluationStack,
        traversal_type: TraversalType,
    ):
        super(TraversalContext, self).__init__(
            config_schema_snapshot=config_schema_snapshot,
            config_type_snap=config_type_snap,
            stack=stack,
        )
        self._config_type = check.inst_param(config_type, "config_type", ConfigType)
        self._traversal_type = check.inst_param(traversal_type, "traversal_type", TraversalType)

    @staticmethod
    def from_config_type(
        config_type: ConfigType,
        stack: EvaluationStack,
        traversal_type: TraversalType,
    ) -> "TraversalContext":
        return TraversalContext(
            config_schema_snapshot=config_type.get_schema_snapshot(),
            config_type_snap=config_type.get_snapshot(),
            config_type=config_type,
            stack=stack,
            traversal_type=traversal_type,
        )

    @property
    def config_type(self) -> ConfigType:
        return self._config_type

    @property
    def traversal_type(self) -> TraversalType:
        return self._traversal_type

    @property
    def do_post_process(self) -> bool:
        return self.traversal_type == TraversalType.RESOLVE_DEFAULTS_AND_POSTPROCESS

    def for_array(self, index: int) -> "TraversalContext":
        check.int_param(index, "index")
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(
                self.config_type_snap.inner_type_key
            ),
            config_type=self.config_type.inner_type,  # type: ignore
            stack=self.stack.for_array_index(index),
            traversal_type=self.traversal_type,
        )

    def for_map(self, key: object) -> "TraversalContext":
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(
                self.config_type_snap.inner_type_key
            ),
            config_type=self.config_type.inner_type,  # type: ignore
            stack=self.stack.for_map_value(key),
            traversal_type=self.traversal_type,
        )

    def for_field(self, field_def: Field, field_name: str) -> "TraversalContext":
        check.inst_param(field_def, "field_def", Field)
        check.str_param(field_name, "field_name")
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(field_def.config_type.key),
            config_type=field_def.config_type,
            stack=self.stack.for_field(field_name),
            traversal_type=self.traversal_type,
        )

    def for_nullable_inner_type(self) -> "TraversalContext":
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(
                self.config_type_snap.inner_type_key
            ),
            config_type=self.config_type.inner_type,  # type: ignore
            stack=self.stack,
            traversal_type=self.traversal_type,
        )

    def for_new_config_type(self, config_type: ConfigType) -> "TraversalContext":
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(config_type.key),
            config_type=config_type,
            stack=self.stack,
            traversal_type=self.traversal_type,
        )
