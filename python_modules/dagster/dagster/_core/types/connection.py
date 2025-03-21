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
    def create_from_sequence(
        cls, seq: Sequence[T], limit: int, cursor: Optional[str] = None
    ) -> "Connection[T]":
        """
        Create a Connection from a sequence of objects.

        Args:
            seq (Sequence[T]): The sequence of objects to paginate

        Returns:
            Connection[T]: A Connection object with the given sequence
        """
        if cursor:
            value = ValueIndexCursor.from_cursor(cursor).value
            if value is None or value not in seq:
                offset = 0
            else:
                offset = seq.index(value) + 1

            seq = seq[offset:]
        else:
            value = None

        has_more = len(seq) > limit
        seq = seq[:limit]

        last_seen_value = seq[-1] if seq else value
        new_cursor = ValueIndexCursor(last_seen_value).to_string()

        return Connection(results=seq, cursor=new_cursor, has_more=has_more)


class ValueIndexCursor:
    """
    Cursor class useful for paginating results based on a last seen value.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        raw = json.dumps({"value": self.value})
        return base64.b64encode(bytes(raw, encoding="utf-8")).decode("utf-8")

    @classmethod
    def from_cursor(cls, cursor: str):
        raw = json.loads(base64.b64decode(cursor).decode("utf-8"))
        if "value" not in raw:
            raise ValueError(f"Invalid cursor: {cursor}")
        return ValueIndexCursor(raw["value"])
