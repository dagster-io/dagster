from dagster._utils.source_position import (
    HasSourcePositionAndKeyPath,
    KeyPath,
    SourcePositionTree,
    populate_source_position_and_key_paths,
)
from dagster._utils.yaml_utils import parse_yaml_with_source_positions


def test_parse_yaml_with_source_positions() -> None:
    source = """
foo:
  bar: 1
  q: [r, s, t]
  baz:
    - a
    - b:
      a: b
  # a comment
  c: "d"
"""

    value_and_tree = parse_yaml_with_source_positions(source, filename="foo.yaml")

    assert value_and_tree.value == {
        "foo": {
            "bar": 1,
            "q": ["r", "s", "t"],
            "baz": ["a", {"b": None, "a": "b"}],
            "c": "d",
        }
    }
    flattened: dict[str, str] = {}

    def visit(path: KeyPath, tree: SourcePositionTree):
        flattened[".".join(str(segment) for segment in path)] = str(tree.position)
        for segment, next_tree in tree.children.items():
            visit([*path, segment], next_tree)

    visit([], value_and_tree.source_position_tree)
    assert flattened == {
        "": "foo.yaml:2",
        "foo": "foo.yaml:2",
        "foo.bar": "foo.yaml:3",
        "foo.q": "foo.yaml:4",
        "foo.q.0": "foo.yaml:4",
        "foo.q.1": "foo.yaml:4",
        "foo.q.2": "foo.yaml:4",
        "foo.baz": "foo.yaml:5",
        "foo.baz.0": "foo.yaml:6",
        "foo.baz.1": "foo.yaml:7",
        "foo.baz.1.b": "foo.yaml:7",
        "foo.baz.1.a": "foo.yaml:8",
        "foo.c": "foo.yaml:10",
    }


def test_populate_source_position_and_key_paths() -> None:
    class CustomStr(str, HasSourcePositionAndKeyPath):
        pass

    class Leaf(HasSourcePositionAndKeyPath):
        def __init__(self):
            self.str1 = "str1"
            self.str2 = CustomStr("str2")

    class Child(HasSourcePositionAndKeyPath):
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

    populate_source_position_and_key_paths(value, parsed.source_position_tree)
    assert value.child.dicts[3][4]._source_position_and_key_path is not None  # noqa: SLF001
    assert (
        str(value.child.dicts[3][4]._source_position_and_key_path.source_position) == "<string>:9"  # noqa: SLF001
    )
    assert value.child.dicts[3][4]._source_position_and_key_path.key_path == [  # noqa: SLF001
        "child",
        "dicts",
        3,
        4,
    ]

    assert value.child.dicts[3][4].str2._source_position_and_key_path is not None  # noqa: SLF001
    assert (
        str(value.child.dicts[3][4].str2._source_position_and_key_path.source_position)  # noqa: SLF001
        == "<string>:11"
    )

    assert not hasattr(value.child.dicts[3][4].str1, "object_mapping_context")
