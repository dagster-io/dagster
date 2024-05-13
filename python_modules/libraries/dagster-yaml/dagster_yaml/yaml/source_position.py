from dataclasses import dataclass
from typing import Optional

KeyPathSegment = str | int
KeyPath = list[KeyPathSegment]


@dataclass(frozen=True)
class LineCol:
    line: int
    col: int


@dataclass(frozen=True)
class SourcePosition:
    filename: str
    start: LineCol
    end: LineCol

    def __str__(self):
        # We could display more information here, like the columns and end positions
        return f"{self.filename}:{self.start.line}"


@dataclass(frozen=True)
class SourcePositionTreeNode:
    position: SourcePosition
    children: dict[KeyPathSegment, "SourcePositionTreeNode"]

    def __hash__(self) -> int:
        return hash((self.position, tuple(sorted(self.children.items()))))

    def lookup(self, key_path: KeyPath) -> Optional[SourcePosition]:
        if len(key_path) == 0:
            return self.position
        head, *tail = key_path
        if head not in self.children:
            return None
        return self.children[head].lookup(tail)
