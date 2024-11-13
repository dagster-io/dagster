from pathlib import Path
from typing import Any, Mapping, NamedTuple, Optional, Sequence, Union, cast

from dagster import _check as check

KeyPathSegment = Union[str, int]
KeyPath = Sequence[KeyPathSegment]


class LineCol(NamedTuple):
    line: int
    col: int


class SourcePosition(NamedTuple):
    filename: str
    start: LineCol
    end: LineCol

    def __str__(self):
        return f"{self.filename}:{self.start.line}"


class SourcePositionTree(NamedTuple):
    """Represents a tree where every node has a SourcePosition."""

    position: SourcePosition
    children: Mapping[KeyPathSegment, "SourcePositionTree"]

    def __hash__(self) -> int:
        return hash((self.position, tuple(sorted(self.children.items()))))

    def lookup(self, key_path: KeyPath) -> Optional[SourcePosition]:
        """Returns the source position of the descendant at the given path."""
        if len(key_path) == 0:
            return self.position
        head, *tail = key_path
        if head not in self.children:
            return None
        return self.children[head].lookup(tail)


class ValueAndSourcePositionTree(NamedTuple):
    """A tree-like object (like a JSON-structured dict) and an accompanying SourcePositionTree.

    Each tree node in the SourcePositionTree is expected to correspond to in value.
    """

    value: Any
    source_position_tree: SourcePositionTree


class SourcePositionAndKeyPath(NamedTuple):
    """Represents a source position and key path within a file.

    Attributes:
        key_path (KeyPath): The path of keys that lead to the current object, where each element in
            the path is either a string (for dict keys) or an integer (for list indices).
        source_position (Optional[SourcePosition]): The source position of the object in the
            document, if available.
    """

    key_path: KeyPath
    source_position: Optional[SourcePosition]


class HasSourcePositionAndKeyPath:
    _source_position_and_key_path: Optional[SourcePositionAndKeyPath] = None

    @property
    def source_position(self) -> SourcePosition:
        """Returns the underlying source position of the blueprint, including
        the source file and line number.
        """
        return check.not_none(check.not_none(self._source_position_and_key_path).source_position)

    @property
    def source_file(self) -> Path:
        """Path to the source file where the blueprint is defined."""
        return Path(check.not_none(self.source_position.filename))

    @property
    def source_file_name(self) -> str:
        """Name of the source file where the blueprint is defined."""
        return self.source_file.name


def populate_source_position_and_key_paths(
    obj: Any,
    source_position_tree: Optional[SourcePositionTree],
    key_path: KeyPath = [],
) -> None:
    """Populate the SourcePositionAndKeyPath for the given object and its children.

    This function recursively traverses the object and its children, setting the
    SourcePositionAndKeyPath on each object that subclasses HasSourcePositionAndKeyPath.

    If the obj is a collection, its children are the elements in the collection. If obj is an
    object, its children are its attributes.

    The SourcePositionAndKeyPath is set based on the provided source position tree, which contains
    the source position information for the object and its children.

    Args:
        obj (Any): The object to populate the source position and key path for.
        source_position_tree (Optional[SourcePositionTree]): The tree node containing the source
            position information for the object and its children.
        key_path (KeyPath): The path of keys that lead to the current object.
    """
    if isinstance(obj, HasSourcePositionAndKeyPath):
        check.invariant(
            obj._source_position_and_key_path is None,  # noqa: SLF001
            "Cannot call populate_source_position_and_key_paths() more than once on the same object",
        )

        if source_position_tree is not None:
            object.__setattr__(
                obj,
                "_source_position_and_key_path",
                SourcePositionAndKeyPath(key_path, source_position_tree.position),
            )

    if source_position_tree is None:
        return

    for child_key_segment, child_tree in source_position_tree.children.items():
        try:
            child_obj = cast(Any, obj)[child_key_segment]
        except TypeError:
            if not isinstance(child_key_segment, str):
                raise
            child_obj = getattr(obj, child_key_segment)

        populate_source_position_and_key_paths(
            child_obj, child_tree, [*key_path, child_key_segment]
        )
