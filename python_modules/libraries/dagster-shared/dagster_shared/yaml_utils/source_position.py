from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, NamedTuple, Optional, Union, cast

import dagster_shared.check as check

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


class YamlSourcedError(NamedTuple):
    file_name: str
    start_line_no: int
    location: str
    snippet: str


OFFSET_LINES_BEFORE = 2
OFFSET_LINES_AFTER = 3


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

    def source_error(
        self,
        yaml_path: KeyPath,
        inline_error_message: str,
        value_error,
    ):
        source_position, source_position_path = self.lookup_closest_and_path(yaml_path, trace=None)

        # Retrieves dotted path representation of the location of the error in the YAML file, e.g.
        # attributes.nested.foo.an_int
        location = ".".join(str(p) for p in yaml_path).split(" at ")[0]

        # Find the first source position that has a different start line than the current source position
        # This is e.g. the parent json key of the current source position
        preceding_source_position = next(
            iter(
                [
                    value
                    for value in reversed(list(source_position_path))
                    if value.start.line < source_position.start.line
                ]
            ),
            source_position,
        )
        if source_position.filename == "<string>":
            code_snippet = ""
        else:
            with open(source_position.filename) as f:
                lines = f.readlines()
            lines_with_line_numbers = list(zip(range(1, len(lines) + 1), lines))

            pre_error_lines = lines_with_line_numbers[
                max(
                    0, preceding_source_position.start.line - OFFSET_LINES_BEFORE
                ) : source_position.start.line
            ]
            source_idx = source_position.start.line - 1
            source_line = (
                lines_with_line_numbers[source_idx][1]
                # parse errors near end of file can spill out of bounds
                if source_idx < len(lines_with_line_numbers)
                else ""
            )
            error_ptr = (
                None,
                _format_indented_error_msg(
                    value_error,
                    source_position,
                    source_line,
                    inline_error_message,
                ),
            )
            post_error_lines = lines_with_line_numbers[
                source_position.start.line : source_position.end.line + OFFSET_LINES_AFTER
            ]

            # Combine the filtered lines with the line numbers, and add empty lines before and after
            lines_with_line_numbers = _prepend_lines_with_line_numbers(
                [(None, ""), *pre_error_lines, error_ptr, *post_error_lines, (None, "")]
            )
            code_snippet = "\n".join(lines_with_line_numbers)

        return YamlSourcedError(
            file_name=source_position.filename,
            start_line_no=source_position.start.line,
            location=location,
            snippet=code_snippet,
        )


def _format_indented_error_msg(
    value_error: bool,
    source_pos: SourcePosition,
    source_line: str,
    msg: str,
) -> str:
    """Format an error message with a caret pointing to the column where the error occurred."""
    inset = source_pos.start.col
    if value_error:
        source_key_end_col = source_pos.end.col
        source_line_end_col = len(source_line)

        approx_middle = source_key_end_col + int((source_line_end_col - source_key_end_col) / 2)
        if approx_middle > source_pos.start.col:  # sanity check we got a reasonable value
            inset = approx_middle

    return " " * (inset - 1) + f"^ {msg}"


def _prepend_lines_with_line_numbers(
    lines_with_numbers: Sequence[tuple[Optional[int], str]],
) -> Sequence[str]:
    """Prepend each line with a line number, right-justified to the maximum line number length.

    Args:
        lines_with_numbers: A sequence of tuples, where the first element is the line number and the
            second element is the line content. Some lines may have a `None` line number, which
            will be rendered as an empty string, used for e.g. inserted error message lines.
    """
    max_line_number_length = max([len(str(n)) for n, _ in lines_with_numbers])
    return [
        f"{(str(n) if n else '').rjust(max_line_number_length)} | {line.rstrip()}"
        for n, line in lines_with_numbers
    ]


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
        """Returns the underlying source position of the object, including
        the source file and line number.
        """
        assert self._source_position_and_key_path
        assert self._source_position_and_key_path.source_position
        return self._source_position_and_key_path.source_position

    @property
    def source_file(self) -> Path:
        """Path to the source file where the object is defined."""
        assert self._source_position_and_key_path
        return Path(self.source_position.filename)

    @property
    def source_file_name(self) -> str:
        """Name of the source file where the object is defined."""
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
            child_obj = cast("Any", obj)[child_key_segment]
        except TypeError:
            if not isinstance(child_key_segment, str):
                raise
            child_obj = getattr(obj, child_key_segment)

        populate_source_position_and_key_paths(
            child_obj, child_tree, [*key_path, child_key_segment]
        )
