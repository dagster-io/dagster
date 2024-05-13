from dagster_yaml.yaml.source_position import KeyPath
from dagster_yaml.yaml.with_source_positions import (
    SourcePositionTreeNode,
    parse_yaml_with_source_positions,
)


def test_parser_smoke() -> None:
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

    value_and_tree_node = parse_yaml_with_source_positions(source, filename="foo.yaml")

    assert value_and_tree_node.value == {
        "foo": {
            "bar": 1,
            "q": ["r", "s", "t"],
            "baz": ["a", {"b": None, "a": "b"}],
            "c": "d",
        }
    }
    flattened: dict[str, str] = {}

    def visit(path: KeyPath, tree: SourcePositionTreeNode):
        flattened[".".join(str(segment) for segment in path)] = str(tree.position)
        for segment, next_tree in tree.children.items():
            visit(path + [segment], next_tree)

    visit([], value_and_tree_node.tree_node)
    assert flattened == {
        "": "foo.yaml:2",
        "foo": "foo.yaml:3",
        "foo.bar": "foo.yaml:3",
        "foo.q": "foo.yaml:4",
        "foo.q.0": "foo.yaml:4",
        "foo.q.1": "foo.yaml:4",
        "foo.q.2": "foo.yaml:4",
        "foo.baz": "foo.yaml:6",
        "foo.baz.0": "foo.yaml:6",
        "foo.baz.1": "foo.yaml:7",
        "foo.baz.1.b": "foo.yaml:7",
        "foo.baz.1.a": "foo.yaml:8",
        "foo.c": "foo.yaml:10",
    }
