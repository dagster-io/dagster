from collections.abc import Mapping, Sequence
from typing import Any, Optional, cast

import dagster._check as check
from dagster._config.config_type import ConfigScalarKind, ConfigType, ConfigTypeKind
from dagster._config.field import Field
from dagster._record import IHaveNew, record, record_custom
from dagster._serdes import whitelist_for_serdes


def get_recursive_type_keys(
    config_type_snap: "ConfigTypeSnap", config_schema_snapshot: "ConfigSchemaSnapshot"
) -> set[str]:
    check.inst_param(config_type_snap, "config_type_snap", ConfigTypeSnap)
    check.inst_param(config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot)
    result_keys = set()
    for type_key in config_type_snap.get_child_type_keys():
        result_keys.add(type_key)
        for recurse_key in get_recursive_type_keys(
            config_schema_snapshot.get_config_snap(type_key), config_schema_snapshot
        ):
            result_keys.add(recurse_key)
    return result_keys


def _ct_name(ct):
    return ct.name


@whitelist_for_serdes(skip_when_empty_fields={"field_aliases"})
@record_custom
class ConfigTypeSnap(IHaveNew):
    kind: ConfigTypeKind
    key: str
    given_name: Optional[str]
    description: Optional[str]
    type_param_keys: Optional[Sequence[str]]  # only valid for closed generics
    enum_values: Optional[Sequence["ConfigEnumValueSnap"]]  # only valid for enums
    fields: Optional[Sequence["ConfigFieldSnap"]]  # only valid for dicts and selectors
    scalar_kind: Optional[ConfigScalarKind]  # only valid for scalars
    field_aliases: Optional[Mapping[str, str]]  # only valid for strict shapes

    # serdes log
    # * Adding scalar_kind
    # * Adding field_aliases
    def __new__(
        cls,
        kind: ConfigTypeKind,
        key: str,
        given_name: Optional[str],
        description: Optional[str],
        type_param_keys: Optional[Sequence[str]],
        enum_values: Optional[Sequence["ConfigEnumValueSnap"]],
        fields: Optional[Sequence["ConfigFieldSnap"]],
        # Old version of object will not have these properties
        scalar_kind: Optional[ConfigScalarKind] = None,
        field_aliases: Optional[Mapping[str, str]] = None,
    ):
        return super().__new__(
            cls,
            kind=kind,
            key=key,
            given_name=given_name,
            description=description,
            type_param_keys=type_param_keys,
            enum_values=enum_values,
            fields=(
                None
                if fields is None
                else sorted(
                    check.list_param(fields, "field", of_type=ConfigFieldSnap),
                    key=_ct_name,
                )
            ),
            scalar_kind=scalar_kind,
            field_aliases=field_aliases or {},
        )

    @property
    def key_type_key(self) -> str:
        """For a type which has keys such as Map, returns the type of the key."""
        # valid for Map, which has its key type as the first entry in type_param_keys
        check.invariant(self.kind == ConfigTypeKind.MAP)

        type_param_keys = check.is_list(self.type_param_keys, of_type=str)
        check.invariant(len(type_param_keys) == 2)
        return type_param_keys[0]

    @property
    def inner_type_key(self) -> str:
        """For container types such as Array or Noneable, the contained type. For a Map, the value type."""
        # valid for Noneable, Map, and Array
        check.invariant(
            self.kind == ConfigTypeKind.NONEABLE
            or self.kind == ConfigTypeKind.ARRAY
            or self.kind == ConfigTypeKind.MAP
        )

        type_param_keys = check.is_list(self.type_param_keys, of_type=str)
        if self.kind == ConfigTypeKind.MAP:
            # For a Map, the inner (value) type is the second entry (the first is the key type)
            check.invariant(len(type_param_keys) == 2)
            return type_param_keys[1]
        else:
            check.invariant(len(type_param_keys) == 1)
            return type_param_keys[0]

    @property
    def scalar_type_key(self) -> str:
        check.invariant(self.kind == ConfigTypeKind.SCALAR_UNION)
        type_param_keys = check.is_list(self.type_param_keys, of_type=str)
        return type_param_keys[0]

    @property
    def non_scalar_type_key(self) -> str:
        check.invariant(self.kind == ConfigTypeKind.SCALAR_UNION)
        type_param_keys = check.is_list(self.type_param_keys, of_type=str)
        return type_param_keys[1]

    def _get_field(self, name: str) -> Optional["ConfigFieldSnap"]:
        check.str_param(name, "name")
        check.invariant(ConfigTypeKind.has_fields(self.kind))
        fields = check.is_list(self.fields, of_type=ConfigFieldSnap)
        for f in fields:
            if f.name == name:
                return f

        return None

    def get_field(self, name: str) -> "ConfigFieldSnap":
        field = self._get_field(name)
        if not field:
            check.failed(f"Field {name} not found")
        return field

    def has_field(self, name: str) -> bool:
        return bool(self._get_field(name))

    @property
    def field_names(self) -> Sequence[str]:
        fields = check.is_list(self.fields, of_type=ConfigFieldSnap)
        # Typing error caught by making is_list typed -- schrockn 2024-06-09
        return [fs.name for fs in fields]  # type: ignore

    def get_child_type_keys(self) -> Sequence[str]:
        if ConfigTypeKind.is_closed_generic(self.kind):
            # all closed generics have type params
            return cast("list[str]", self.type_param_keys)
        elif ConfigTypeKind.has_fields(self.kind):
            return [
                field.type_key
                for field in cast("list[ConfigFieldSnap]", check.not_none(self.fields))
            ]
        else:
            return []

    def has_enum_value(self, value: object) -> bool:
        check.invariant(self.kind == ConfigTypeKind.ENUM)
        for enum_value in cast("list[ConfigEnumValueSnap]", self.enum_values):
            if enum_value.value == value:
                return True
        return False


@whitelist_for_serdes
@record
class ConfigEnumValueSnap:
    value: str
    description: Optional[str]


@whitelist_for_serdes
@record
class ConfigFieldSnap:
    name: Optional[str]
    type_key: str
    is_required: bool
    default_provided: bool
    default_value_as_json_str: Optional[str]
    description: Optional[str]


def snap_from_field(name: str, field: Field):
    return ConfigFieldSnap(
        name=name,
        type_key=field.config_type.key,
        is_required=field.is_required,
        default_provided=field.default_provided,
        default_value_as_json_str=(
            field.default_value_as_json_str if field.default_provided else None
        ),
        description=field.description,
    )


# type-ignores here are temporary until config type system overhauled
def snap_from_config_type(config_type: ConfigType) -> ConfigTypeSnap:
    return ConfigTypeSnap(
        key=config_type.key,
        given_name=config_type.given_name,
        kind=config_type.kind,
        description=config_type.description,
        type_param_keys=(
            [ct.key for ct in config_type.type_params]
            if config_type.type_params
            # jam scalar union types into type_param_keys
            else (
                [config_type.scalar_type.key, config_type.non_scalar_type.key]  # type: ignore
                if config_type.kind == ConfigTypeKind.SCALAR_UNION
                else None
            )
        ),
        enum_values=(
            [
                ConfigEnumValueSnap(value=ev.config_value, description=ev.description)
                for ev in config_type.enum_values  # type: ignore
            ]
            if config_type.kind == ConfigTypeKind.ENUM
            else None
        ),
        fields=(
            [snap_from_field(name, field) for name, field in config_type.fields.items()]  # type: ignore
            if ConfigTypeKind.has_fields(config_type.kind)
            else None
        ),
        scalar_kind=config_type.scalar_kind if config_type.kind == ConfigTypeKind.SCALAR else None,  # type: ignore
        field_aliases=(
            config_type.field_aliases  # type: ignore
            if config_type.kind == ConfigTypeKind.STRICT_SHAPE
            else None
        ),
    )


@whitelist_for_serdes
@record
class ConfigSchemaSnapshot:
    all_config_snaps_by_key: Mapping[str, ConfigTypeSnap]

    @property
    def all_config_keys(self) -> Sequence[str]:
        return list(self.all_config_snaps_by_key.keys())

    def get_config_snap(self, key: str) -> ConfigTypeSnap:
        check.str_param(key, "key")
        return self.all_config_snaps_by_key[key]

    def has_config_snap(self, key: str) -> bool:
        check.str_param(key, "key")
        return key in self.all_config_snaps_by_key


def minimal_config_for_type_snap(
    config_schema_snap: ConfigSchemaSnapshot, config_type_snap: ConfigTypeSnap
) -> Any:
    check.inst_param(config_schema_snap, "config_schema_snap", ConfigSchemaSnapshot)
    check.inst_param(config_type_snap, "config_type_snap", ConfigTypeSnap)

    if ConfigTypeKind.has_fields(config_type_snap.kind):
        default_dict = {}
        if ConfigTypeKind.is_selector(config_type_snap.kind):
            return "<selector>"
        for field in config_type_snap.fields:  # type: ignore
            if not field.is_required:
                continue

            default_dict[field.name] = minimal_config_for_type_snap(
                config_schema_snap, config_schema_snap.get_config_snap(field.type_key)
            )
        return default_dict
    elif config_type_snap.kind == ConfigTypeKind.ANY:
        return "AnyType"
    elif config_type_snap.kind == ConfigTypeKind.SCALAR:
        defaults = {"String": "...", "Int": 0, "Float": 0.0, "Bool": True}

        return defaults.get(config_type_snap.given_name, "<unknown>")  # type: ignore
    elif config_type_snap.kind == ConfigTypeKind.ARRAY:
        return []
    elif config_type_snap.kind == ConfigTypeKind.MAP:
        return {}
    elif config_type_snap.kind == ConfigTypeKind.ENUM:
        # guard against the edge case that an enum is defined with zero options
        return (
            config_type_snap.enum_values[0].value if config_type_snap.enum_values else "<unknown>"
        )
    elif config_type_snap.kind == ConfigTypeKind.SCALAR_UNION:
        return minimal_config_for_type_snap(
            config_schema_snap,
            config_schema_snap.get_config_snap(config_type_snap.type_param_keys[0]),  # type: ignore
        )
    else:
        return "<unknown>"
