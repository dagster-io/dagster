from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, NamedTuple, Optional, Union

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

    def lookup_closest_and_path(
        self, key_path: KeyPath, trace: Optional[Sequence[SourcePosition]]
    ) -> tuple[SourcePosition, Sequence[SourcePosition]]:
        """Returns the source position of the descendant at the given path. If the path does not
        exist, returns the source position of the nearest ancestor.
        """
        trace = [*trace, self.position] if trace else [self.position]
        if len(key_path) == 0:
            return self.position, trace
        head, *tail = key_path
        if head not in self.children:
            return self.position, trace
        return self.children[head].lookup_closest_and_path(tail, trace)


class ValueAndSourcePositionTree(NamedTuple):
    """A tree-like object (like a JSON-structured dict) and an accompanying SourcePositionTree.

    Each tree node in the SourcePositionTree is expected to correspond to in value.
    """

    value: Any
    source_position_tree: SourcePositionTree


class SourcePositionAndKeyPath(NamedTuple):
    """Represents a source position and key path within a file.

    Args:
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
        assert self._source_position_and_key_path
        assert self._source_position_and_key_path.source_position
        return self._source_position_and_key_path.source_position

    @property
    def source_file(self) -> Path:
        """Path to the source file where the blueprint is defined."""
        assert self._source_position_and_key_path
        return Path(self.source_position.filename)

    @property
    def source_file_name(self) -> str:
        """Name of the source file where the blueprint is defined."""
        return self.source_file.name
