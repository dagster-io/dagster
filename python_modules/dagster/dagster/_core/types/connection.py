import base64
from typing import (
    Generic,
    Optional,
    Sequence,
)
from dagster._seven import json

from typing_extensions import TypeVar

T = TypeVar("T")


class Connection(Generic[T]):
    """
    A wrapper for paginated results of type T.

    Attributes:
        results (Sequence[T]): The sequence of returned objects
        cursor (Optional[str]): Pagination cursor for fetching next page
        has_more (bool): Whether more results are available
    """

    def __init__(self, results: Sequence[T], cursor: str, has_more: bool = False):
        self.results = results
        self.cursor = cursor
        self.has_more = has_more

    @classmethod
    def create_from_offset_list(
        cls, seq: Sequence[T], cursor: Optional[str] = None, limit: Optional[int] = None
    ) -> "Connection[T]":
        """
        Create a Connection from a sequence of objects.

        Args:
            seq (Sequence[T]): The sequence of objects to paginate

        Returns:
            Connection[T]: A Connection object with the given sequence
        """
        if cursor:
            offset = OffsetCursor.from_cursor(cursor).offset
            seq = seq[offset:]
        else:
            offset = 0

        has_more = len(seq) > limit if limit else False
        seq = seq[:limit] if limit else seq

        new_cursor = str(OffsetCursor(offset + len(seq)))
        return Connection(results=seq, cursor=new_cursor, has_more=has_more)


class OffsetCursor:
    def __init__(self, offset: int):
        self.offset = offset

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        raw = json.dumps({"offset": self.offset})
        return base64.b64encode(bytes(raw, encoding="utf-8")).decode("utf-8")

    @classmethod
    def from_cursor(cls, cursor: str):
        raw = json.loads(base64.b64decode(cursor).decode("utf-8"))
        if "offset" not in raw:
            raise ValueError(f"Invalid cursor: {cursor}")
        try:
            offset = int(raw["offset"])
        except ValueError:
            raise ValueError(f"Invalid cursor: {cursor}")
        return OffsetCursor(offset)
