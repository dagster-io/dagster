import base64
from typing import NamedTuple, Sequence

from dagster._seven import json

LOG_STREAM_COMPLETED_SIGIL = "LOGS COMPLETED"


class JSONLogLineCursor(NamedTuple):
    """Representation of an JSON compute log cursor, keeping track of the log query state.
    The compute logs are stored in multiple files in the same direcotry. The cursor keeps
    track of the file name and the number of lines read so far.

    line=-1 means that the entire file has been read and the next file should be read. This covers the
    case when and entire file has been read, but the next file does not exist in storage yet.
    line=0 means no lines from the file have been read.
    line=n means lines 0 through n-1 have been read from the file.
    """

    log_key: Sequence[str]
    line: int  # maybe rename line_offset?
    has_more: bool

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        raw = json.dumps({"log_key": self.log_key, "line": self.line, "has_more": self.has_more})
        return base64.b64encode(bytes(raw, encoding="utf-8")).decode("utf-8")

    @staticmethod
    def parse(cursor_str: str) -> "JSONLogLineCursor":
        raw = json.loads(base64.b64decode(cursor_str).decode("utf-8"))
        return JSONLogLineCursor(raw["log_key"], raw["line"], raw["has_more"])
