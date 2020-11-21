from enum import Enum

from dagster import check

from .config_type import ConfigType
from .field import Field
from .iterate_types import config_schema_snapshot_from_config_type, iterate_config_types
from .snap import ConfigFieldSnap, ConfigSchemaSnapshot, ConfigTypeSnap, snap_from_config_type
from .stack import EvaluationStack


class TraversalType(Enum):
    VALIDATE = "VALIDATE"
    RESOLVE_DEFAULTS = "RESOLVE_DEFAULTS"
    RESOLVE_DEFAULTS_AND_POSTPROCESS = "RESOLVE_DEFAULTS_AND_POSTPROCESS"


class ContextData:
    __slots__ = ["_config_schema_snapshot", "_config_type_snap", "_stack"]

    def __init__(self, config_schema_snapshot, config_type_snap, stack):
        self._config_schema_snapshot = check.opt_inst_param(
            config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot
        )

        self._config_type_snap = check.opt_inst_param(
            config_type_snap, "config_type_snap", ConfigTypeSnap
        )

        self._stack = check.inst_param(stack, "stack", EvaluationStack)

    @property
    def config_schema_snapshot(self):
        return self._config_schema_snapshot

    @property
    def config_type_snap(self):
        return self._config_type_snap

    @property
    def config_type_key(self):
        return self._config_type_snap.key

    @property
    def stack(self):
        return self._stack


class ValidationContext(ContextData):
    def for_field_snap(self, field_snap):
        check.inst_param(field_snap, "field_snap", ConfigFieldSnap)
        return ValidationContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(field_snap.type_key),
            stack=self.stack.for_field(field_snap.name),
        )

    def for_array(self, index):
        check.int_param(index, "index")
        return ValidationContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(
                self.config_type_snap.inner_type_key
            ),
            stack=self.stack.for_array_index(index),
        )

    def for_new_config_type_key(self, config_type_key):
        check.str_param(config_type_key, "config_type_key")
        return ValidationContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(config_type_key),
            stack=self.stack,
        )

    def for_nullable_inner_type(self):
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
        config_schema_snapshot,
        config_type_snap,
        config_type,
        stack,
        traversal_type,
        all_config_types,
    ):
        super(TraversalContext, self).__init__(
            config_schema_snapshot=config_schema_snapshot,
            config_type_snap=config_type_snap,
            stack=stack,
        )
        self._config_type = check.inst_param(config_type, "config_type", ConfigType)
        self._traversal_type = check.inst_param(traversal_type, "traversal_type", TraversalType)
        self._all_config_types = check.dict_param(all_config_types, "all_config_types")

    @staticmethod
    def from_config_type(config_type, stack, traversal_type):
        all_config_types = list(iterate_config_types(config_type))
        config_schema_snapshot = config_schema_snapshot_from_config_type(config_type)
        return TraversalContext(
            config_schema_snapshot=config_schema_snapshot,
            config_type_snap=snap_from_config_type(config_type),
            config_type=config_type,
            stack=stack,
            traversal_type=traversal_type,
            all_config_types={ct.key: ct for ct in all_config_types},
        )

    @property
    def all_config_types(self):
        return self._all_config_types

    @property
    def config_type(self):
        return self._config_type

    @property
    def traversal_type(self):
        return self._traversal_type

    @property
    def do_post_process(self):
        return self.traversal_type == TraversalType.RESOLVE_DEFAULTS_AND_POSTPROCESS

    def for_array(self, index):
        check.int_param(index, "index")
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(
                self.config_type_snap.inner_type_key
            ),
            config_type=self.config_type.inner_type,
            stack=self.stack.for_array_index(index),
            traversal_type=self.traversal_type,
            all_config_types=self.all_config_types,
        )

    def for_field(self, field_def, field_name):
        check.inst_param(field_def, "field_def", Field)
        check.str_param(field_name, "field_name")
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(field_def.config_type.key),
            config_type=field_def.config_type,
            stack=self.stack.for_field(field_name),
            traversal_type=self.traversal_type,
            all_config_types=self.all_config_types,
        )

    def for_nullable_inner_type(self):
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(
                self.config_type_snap.inner_type_key
            ),
            config_type=self.config_type.inner_type,
            stack=self.stack,
            traversal_type=self.traversal_type,
            all_config_types=self.all_config_types,
        )

    def for_new_config_type(self, config_type):
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(config_type.key),
            config_type=config_type,
            stack=self.stack,
            traversal_type=self.traversal_type,
            all_config_types=self.all_config_types,
        )
