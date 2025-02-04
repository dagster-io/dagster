import dagster._check as check
from dagster._config.config_type import ConfigType
from dagster._config.field import Field
from dagster._config.snap import ConfigFieldSnap, ConfigSchemaSnapshot, ConfigTypeSnap
from dagster._config.stack import EvaluationStackEntry
from dagster._record import record


@record
class ContextData:
    config_schema_snapshot: ConfigSchemaSnapshot
    config_type_snap: ConfigTypeSnap
    stack: EvaluationStackEntry

    @property
    def config_type_key(self) -> str:
        return self.config_type_snap.key


@record
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


@record
class TraversalContext(ContextData):
    config_type: ConfigType
    do_post_process: bool

    @staticmethod
    def from_config_type(
        config_type: ConfigType,
        stack: EvaluationStackEntry,
        do_post_process: bool,
    ) -> "TraversalContext":
        return TraversalContext(
            config_schema_snapshot=config_type.schema_snapshot,
            config_type_snap=config_type.snapshot,
            config_type=config_type,
            stack=stack,
            do_post_process=do_post_process,
        )

    def for_array(self, index: int) -> "TraversalContext":
        check.int_param(index, "index")
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(
                self.config_type_snap.inner_type_key
            ),
            config_type=self.config_type.inner_type,  # type: ignore
            stack=self.stack.for_array_index(index),
            do_post_process=self.do_post_process,
        )

    def for_map(self, key: object) -> "TraversalContext":
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(
                self.config_type_snap.inner_type_key
            ),
            config_type=self.config_type.inner_type,  # type: ignore
            stack=self.stack.for_map_value(key),
            do_post_process=self.do_post_process,
        )

    def for_field(self, field_def: Field, field_name: str) -> "TraversalContext":
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(field_def.config_type.key),
            config_type=field_def.config_type,
            stack=self.stack.for_field(field_name),
            do_post_process=self.do_post_process,
        )

    def for_nullable_inner_type(self) -> "TraversalContext":
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(
                self.config_type_snap.inner_type_key
            ),
            config_type=self.config_type.inner_type,  # type: ignore
            stack=self.stack,
            do_post_process=self.do_post_process,
        )

    def for_new_config_type(self, config_type: ConfigType) -> "TraversalContext":
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_snap(config_type.key),
            config_type=config_type,
            stack=self.stack,
            do_post_process=self.do_post_process,
        )
