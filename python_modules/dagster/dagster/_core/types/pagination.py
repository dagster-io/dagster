import base64
from typing import (
    Any,
    Generic,
    Optional,
    Sequence,
)
from dagster._record import record
from dagster._serdes import whitelist_for_serdes, deserialize_value, serialize_value

from typing_extensions import TypeVar

T = TypeVar("T")


@record
class PaginatedResults(Generic[T]):
    results: Sequence[T]
    cursor: str
    has_more: bool

    """
    A wrapper for paginated connection results of type T.

    Attributes:
        results (Sequence[T]): The sequence of returned objects
        cursor (Optional[str]): Pagination cursor for fetching next page
        has_more (bool): Whether more results are available
    """

    @classmethod
    def create_from_sequence(
        cls, seq: Sequence[T], limit: int, ascending: bool, cursor: Optional[str] = None
    ) -> "PaginatedResults[T]":
        """
        Create a PaginatedResults from a sequence of objects.

        Args:
            seq (Sequence[T]): The sequence of objects to paginate

        Returns:
            PaginatedResults[T]: A PaginatedResults object with the given sequence
        """
        seq = seq if ascending else list(reversed(seq))
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
        new_cursor = ValueIndexCursor(value=last_seen_value).to_string()

        return PaginatedResults(results=seq, cursor=new_cursor, has_more=has_more)


@whitelist_for_serdes
@record
class ValueIndexCursor:
    """
    Cursor class useful for paginating results based on a last seen value.
    """

    value: Any

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        string_serialized = serialize_value(self)
        return base64.b64encode(bytes(string_serialized, encoding="utf-8")).decode(
            "utf-8"
        )

    @classmethod
    def from_cursor(cls, cursor: str):
        return deserialize_value(base64.b64decode(cursor).decode("utf-8"), cls)


@whitelist_for_serdes
@record
class StorageIdCursor:
    storage_id: int

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        string_serialized = serialize_value(self)
        return base64.b64encode(bytes(string_serialized, encoding="utf-8")).decode(
            "utf-8"
        )

    @classmethod
    def from_cursor(cls, cursor: str):
        return deserialize_value(base64.b64decode(cursor).decode("utf-8"), cls)
