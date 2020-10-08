from dagster import Dict, InputDefinition, List, OutputDefinition, Set, Tuple, pipeline, solid
from dagster.core.snap import build_dagster_type_namespace_snapshot
from dagster.core.types.dagster_type import ALL_RUNTIME_BUILTINS, create_string_type


def test_simple_pipeline_input_dagster_type_namespace():
    SomethingType = create_string_type("SomethingType", description="desc")

    @solid(input_defs=[InputDefinition("something", SomethingType)])
    def take_something(_, something):
        return something

    @pipeline
    def simple():
        take_something()

    namespace = build_dagster_type_namespace_snapshot(simple)
    type_snap = namespace.get_dagster_type_snap("SomethingType")
    assert type_snap
    assert type_snap.key == "SomethingType"
    assert type_snap.name == "SomethingType"
    assert type_snap.display_name == "SomethingType"
    assert type_snap.description == "desc"
    assert type_snap.is_builtin is False
    assert type_snap.type_param_keys == []
    assert type_snap.loader_schema_key == SomethingType.loader_schema_key
    assert type_snap.materializer_schema_key == SomethingType.materializer_schema_key


def test_simple_pipeline_output_dagster_type_namespace():
    SomethingType = create_string_type("SomethingType")

    @solid(output_defs=[OutputDefinition(SomethingType)])
    def take_something(_):
        return "something"

    @pipeline
    def simple():
        take_something()

    namespace = build_dagster_type_namespace_snapshot(simple)
    assert namespace.get_dagster_type_snap("SomethingType")


def test_kitchen_sink_of_collection_types_snaps():
    SomethingType = create_string_type("SomethingType")

    @solid(input_defs=[InputDefinition("somethings", List[SomethingType])])
    def take_list(_, somethings):
        return somethings

    @solid(input_defs=[InputDefinition("somethings", Set[SomethingType])])
    def take_set(_, somethings):
        return somethings

    # dict cannot be input without dep
    # see https://github.com/dagster-io/dagster/issues/2272
    @solid(output_defs=[OutputDefinition(Dict[str, SomethingType])])
    def return_dict(_):
        return {}

    @solid(input_defs=[InputDefinition("somethings", Tuple[str, SomethingType])])
    def take_tuple(_, somethings):
        return somethings

    @pipeline
    def simple():
        take_list()
        take_set()
        return_dict()
        take_tuple()

    namespace = build_dagster_type_namespace_snapshot(simple)

    assert namespace.get_dagster_type_snap(List[SomethingType].key)
    list_something = namespace.get_dagster_type_snap(List[SomethingType].key)
    assert len(list_something.type_param_keys) == 1
    assert list_something.type_param_keys[0] == SomethingType.key
    assert list_something.display_name == "[SomethingType]"

    assert namespace.get_dagster_type_snap(Set[SomethingType].key)
    something_set = namespace.get_dagster_type_snap(Set[SomethingType].key)
    assert len(something_set.type_param_keys) == 1
    assert something_set.type_param_keys[0] == SomethingType.key
    assert something_set.display_name == "Set[SomethingType]"

    assert namespace.get_dagster_type_snap(Dict[str, SomethingType].key)
    something_dict = namespace.get_dagster_type_snap(Dict[str, SomethingType].key)
    assert len(something_dict.type_param_keys) == 2
    assert something_dict.type_param_keys[0] == "String"
    assert something_dict.type_param_keys[1] == SomethingType.key
    assert something_dict.display_name == "Dict[String,SomethingType]"

    assert namespace.get_dagster_type_snap(Tuple[str, SomethingType].key)
    something_tuple = namespace.get_dagster_type_snap(Tuple[str, SomethingType].key)
    assert len(something_tuple.type_param_keys) == 2
    assert something_tuple.type_param_keys[0] == "String"
    assert something_tuple.type_param_keys[1] == SomethingType.key
    assert something_tuple.display_name == "Tuple[String,SomethingType]"


def test_kitchen_sink_of_builtins():
    @solid
    def noop(_):
        pass

    @pipeline
    def simple():
        noop()

    namespace = build_dagster_type_namespace_snapshot(simple)

    for builtin in ALL_RUNTIME_BUILTINS:
        assert namespace.get_dagster_type_snap(builtin.key)
