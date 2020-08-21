from dagster import (
    Array,
    Field,
    ModeDefinition,
    Noneable,
    ScalarUnion,
    Selector,
    Shape,
    pipeline,
    resource,
    solid,
)
from dagster.config.config_type import ConfigTypeKind
from dagster.config.field import resolve_to_config_type
from dagster.core.snap import build_config_schema_snapshot, snap_from_config_type
from dagster.serdes import (
    deserialize_json_to_dagster_namedtuple,
    deserialize_value,
    serialize_dagster_namedtuple,
    serialize_pp,
)


def snap_from_dagster_type(dagster_type):
    return snap_from_config_type(resolve_to_config_type(dagster_type))


def test_basic_int_snap():
    int_snap = snap_from_dagster_type(int)
    assert int_snap.given_name == "Int"
    assert int_snap.key == "Int"
    assert int_snap.kind == ConfigTypeKind.SCALAR
    assert int_snap.enum_values is None
    assert int_snap.fields is None


def test_basic_dict():
    dict_snap = snap_from_dagster_type({"foo": int})
    assert dict_snap.key.startswith("Shape.")
    assert dict_snap.given_name is None
    child_type_keys = dict_snap.get_child_type_keys()
    assert child_type_keys
    assert len(child_type_keys) == 1
    assert child_type_keys[0] == "Int"
    assert child_type_keys[0]

    assert dict_snap.fields and len(dict_snap.fields) == 1

    field = dict_snap.fields[0]
    assert field.name == "foo"


def test_field_things():
    dict_snap = snap_from_dagster_type(
        {
            "req": int,
            "opt": Field(int, is_required=False),
            "opt_with_default": Field(int, is_required=False, default_value=2),
            "req_with_desc": Field(int, description="A desc"),
        }
    )

    assert dict_snap.fields and len(dict_snap.fields) == 4

    field_snap_dict = {field_snap.name: field_snap for field_snap in dict_snap.fields}

    assert field_snap_dict["req"].is_required is True
    assert field_snap_dict["req"].description is None
    assert field_snap_dict["opt"].is_required is False
    assert field_snap_dict["opt"].default_provided is False
    assert field_snap_dict["opt"].default_value_as_json_str is None
    assert field_snap_dict["opt_with_default"].is_required is False
    assert field_snap_dict["opt_with_default"].default_provided is True
    assert deserialize_value(field_snap_dict["opt_with_default"].default_value_as_json_str) == 2

    assert field_snap_dict["req_with_desc"].is_required is True
    assert field_snap_dict["req_with_desc"].description == "A desc"


def test_basic_list():
    list_snap = snap_from_dagster_type(Array(int))
    assert list_snap.key.startswith("Array")
    child_type_keys = list_snap.get_child_type_keys()
    assert child_type_keys
    assert len(child_type_keys) == 1
    assert child_type_keys[0] == "Int"


def test_basic_optional():
    optional_snap = snap_from_dagster_type(Noneable(int))
    assert optional_snap.key.startswith("Noneable")

    child_type_keys = optional_snap.get_child_type_keys()
    assert child_type_keys
    assert len(child_type_keys) == 1
    assert child_type_keys[0] == "Int"
    assert optional_snap.kind == ConfigTypeKind.NONEABLE
    assert optional_snap.enum_values is None


def test_basic_list_list():
    list_snap = snap_from_dagster_type([[int]])
    assert list_snap.key.startswith("Array")
    child_type_keys = list_snap.get_child_type_keys()
    assert child_type_keys
    assert len(child_type_keys) == 1
    assert child_type_keys[0] == "Array.Int"
    assert list_snap.enum_values is None


def test_list_of_dict():
    inner_dict_dagster_type = Shape({"foo": Field(str)})
    list_of_dict_snap = snap_from_dagster_type([inner_dict_dagster_type])

    assert list_of_dict_snap.key.startswith("Array")
    child_type_keys = list_of_dict_snap.get_child_type_keys()
    assert child_type_keys
    assert len(child_type_keys) == 1
    assert child_type_keys[0].startswith("Shape")


def test_selector_of_things():
    selector_snap = snap_from_dagster_type(Selector({"bar": Field(int)}))
    assert selector_snap.key.startswith("Selector")
    assert selector_snap.kind == ConfigTypeKind.SELECTOR
    assert selector_snap.fields and len(selector_snap.fields) == 1
    field_snap = selector_snap.fields[0]
    assert field_snap.name == "bar"
    assert field_snap.type_key == "Int"


def test_kitchen_sink():
    kitchen_sink = resolve_to_config_type(
        [
            {
                "opt_list_of_int": Field(int, is_required=False),
                "nested_dict": {
                    "list_list": [[int]],
                    "nested_selector": Field(
                        Selector({"some_field": int, "more_list": Noneable([bool])})
                    ),
                },
            }
        ]
    )

    kitchen_sink_snap = snap_from_dagster_type(kitchen_sink)

    rehydrated_snap = deserialize_json_to_dagster_namedtuple(
        serialize_dagster_namedtuple(kitchen_sink_snap)
    )
    assert kitchen_sink_snap == rehydrated_snap


def test_simple_pipeline_smoke_test():
    @solid
    def solid_without_config(_):
        pass

    @pipeline
    def single_solid_pipeline():
        solid_without_config()

    config_schema_snapshot = build_config_schema_snapshot(single_solid_pipeline)
    assert config_schema_snapshot.all_config_snaps_by_key

    serialized = serialize_dagster_namedtuple(config_schema_snapshot)
    rehydrated_config_schema_snapshot = deserialize_json_to_dagster_namedtuple(serialized)
    assert config_schema_snapshot == rehydrated_config_schema_snapshot


def test_check_solid_config_correct():
    @solid(config_schema={"foo": str})
    def solid_with_config(_):
        pass

    @pipeline
    def single_solid_pipeline():
        solid_with_config()

    solid_config_key = solid_with_config.config_schema.config_type.key

    config_snaps = build_config_schema_snapshot(single_solid_pipeline).all_config_snaps_by_key

    assert solid_config_key in config_snaps

    solid_config_snap = config_snaps[solid_config_key]

    assert solid_config_snap.kind == ConfigTypeKind.STRICT_SHAPE
    assert len(solid_config_snap.fields) == 1

    foo_field = solid_config_snap.fields[0]

    assert foo_field.name == "foo"
    assert foo_field.type_key == "String"


def test_check_solid_list_list_config_correct():
    @solid(config_schema={"list_list_int": [[{"bar": int}]]})
    def solid_with_config(_):
        pass

    @pipeline
    def single_solid_pipeline():
        solid_with_config()

    solid_config_key = solid_with_config.config_schema.config_type.key

    config_snaps = build_config_schema_snapshot(single_solid_pipeline).all_config_snaps_by_key
    assert solid_config_key in config_snaps
    solid_config_snap = config_snaps[solid_config_key]

    assert solid_config_snap.kind == ConfigTypeKind.STRICT_SHAPE
    assert len(solid_config_snap.fields) == 1

    list_list_field = solid_config_snap.fields[0]

    list_list_type_key = list_list_field.type_key

    assert list_list_type_key.startswith("Array.Array.")

    list_list_type = config_snaps[list_list_type_key]

    assert list_list_type.kind == ConfigTypeKind.ARRAY
    list_snap = config_snaps[list_list_type.inner_type_key]
    assert list_snap.kind == ConfigTypeKind.ARRAY
    assert config_snaps[list_snap.inner_type_key].kind == ConfigTypeKind.STRICT_SHAPE


def test_kitchen_sink_break_out():
    @solid(
        config_schema=[
            {
                "opt_list_of_int": Field([int], is_required=False),
                "nested_dict": {
                    "list_list": [[int]],
                    "nested_selector": Selector(
                        {"some_field": int, "noneable_list": Noneable([bool])}
                    ),
                },
            }
        ]
    )
    def solid_with_kitchen_sink_config(_):
        pass

    @pipeline
    def single_solid_pipeline():
        solid_with_kitchen_sink_config()

    config_snaps = build_config_schema_snapshot(single_solid_pipeline).all_config_snaps_by_key

    solid_config_key = solid_with_kitchen_sink_config.config_schema.config_type.key
    assert solid_config_key in config_snaps
    solid_config_snap = config_snaps[solid_config_key]

    assert solid_config_snap.kind == ConfigTypeKind.ARRAY

    dict_within_list = config_snaps[solid_config_snap.inner_type_key]

    assert len(dict_within_list.fields) == 2

    opt_field = dict_within_list.get_field("opt_list_of_int")

    assert opt_field.is_required is False
    assert config_snaps[opt_field.type_key].kind == ConfigTypeKind.ARRAY

    nested_dict = config_snaps[dict_within_list.get_field("nested_dict").type_key]
    assert len(nested_dict.fields) == 2
    nested_selector = config_snaps[nested_dict.get_field("nested_selector").type_key]
    noneable_list_bool = config_snaps[nested_selector.get_field("noneable_list").type_key]
    assert noneable_list_bool.kind == ConfigTypeKind.NONEABLE
    list_bool = config_snaps[noneable_list_bool.inner_type_key]
    assert list_bool.kind == ConfigTypeKind.ARRAY


def test_multiple_modes():
    @solid
    def noop_solid(_):
        pass

    @resource(config_schema={"a": int})
    def a_resource(_):
        pass

    @resource(config_schema={"b": int})
    def b_resource(_):
        pass

    @pipeline(
        mode_defs=[
            ModeDefinition(name="mode_a", resource_defs={"resource": a_resource}),
            ModeDefinition(name="mode_b", resource_defs={"resource": b_resource}),
        ]
    )
    def modez():
        noop_solid()

    config_snaps = build_config_schema_snapshot(modez).all_config_snaps_by_key

    assert a_resource.config_schema.config_type.key in config_snaps
    assert b_resource.config_schema.config_type.key in config_snaps

    assert get_config_snap(modez, a_resource.config_schema.config_type.key)
    assert get_config_snap(modez, b_resource.config_schema.config_type.key)


def get_config_snap(pipeline_def, key):
    return pipeline_def.get_pipeline_snapshot().config_schema_snapshot.get_config_snap(key)


def test_scalar_union():
    # Requiring resolve calls is bad: https://github.com/dagster-io/dagster/issues/2266
    @solid(
        config_schema=ScalarUnion(resolve_to_config_type(str), resolve_to_config_type({"bar": str}))
    )
    def solid_with_config(_):
        pass

    @pipeline
    def single_solid_pipeline():
        solid_with_config()

    config_snaps = build_config_schema_snapshot(single_solid_pipeline).all_config_snaps_by_key

    scalar_union_key = solid_with_config.config_schema.config_type.key

    assert scalar_union_key in config_snaps

    assert config_snaps[config_snaps[scalar_union_key].scalar_type_key].key == "String"
    assert (
        config_snaps[config_snaps[scalar_union_key].non_scalar_type_key].kind
        == ConfigTypeKind.STRICT_SHAPE
    )


def test_historical_config_type_snap(snapshot):
    old_snap_json = """{"__class__": "ConfigTypeSnap", "description": "", "enum_values": [], "fields": [], "given_name": "kjdkfjdkfjdkj", "key": "ksjdkfjdkfjd", "kind": {"__enum__": "ConfigTypeKind.STRICT_SHAPE"}, "type_param_keys": []}"""

    old_snap = deserialize_json_to_dagster_namedtuple(old_snap_json)

    snapshot.assert_match(serialize_pp(old_snap))
