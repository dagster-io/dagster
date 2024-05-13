from dagster_yaml.yaml.object_mapping import (
    HasObjectMappingContext,
    populate_object_mapping_context,
)
from dagster_yaml.yaml.with_source_positions import parse_yaml_with_source_positions


def test_object_mapping_smoke() -> None:
    class CustomStr(str, HasObjectMappingContext):
        pass

    class Leaf(HasObjectMappingContext):
        def __init__(self):
            self.str1 = "str1"
            self.str2 = CustomStr("str2")

    class Child(HasObjectMappingContext):
        def __init__(self):
            self.dicts = {1: {2: Leaf()}, 3: {4: Leaf()}, 5: {6: Leaf()}}

    class Root:
        def __init__(self):
            self.child = Child()

    parsed = parse_yaml_with_source_positions(
        """
child:
  dicts:
    1:
      2:
        str1: str1
        str2: str2
    3:
      4:
        str1: str1
        str2: str2
    5:
      6:
        str1: str1
        str2: str2
"""
    )

    value = Root()
    populate_object_mapping_context(value, parsed.tree_node)

    assert value.child.dicts[3][4]._object_mapping_context is not None  # noqa: SLF001
    assert str(value.child.dicts[3][4]._object_mapping_context.source_position) == "<string>:10"  # noqa: SLF001
    assert value.child.dicts[3][4]._object_mapping_context.key_path == ["child", "dicts", 3, 4]  # noqa: SLF001

    assert value.child.dicts[3][4].str2._object_mapping_context is not None  # noqa: SLF001
    assert (
        str(value.child.dicts[3][4].str2._object_mapping_context.source_position) == "<string>:11"  # noqa: SLF001
    )

    assert not hasattr(value.child.dicts[3][4].str1, "object_mapping_context")
