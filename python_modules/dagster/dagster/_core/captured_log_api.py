import base64
from collections.abc import Sequence
from typing import NamedTuple

from dagster_shared.seven import json


class LogLineCursor(NamedTuple):
    """Representation of a log line cursor, to keep track of the place in the logs.
    The captured logs are stored in multiple files in the same direcotry. The cursor keeps
    track of the file name and the number of lines read so far.

    line=-1 means that the entire file has been read and the next file should be read. This covers the
    case when and entire file has been read, but the next file does not exist in storage yet.
    line=0 means no lines from the file have been read.
    line=n means lines 0 through n-1 have been read from the file.

    has_more_now indicates if there are more log lines that can be read immediately. If the process writing
    logs is still running, but has not writen a log file, has_more_now will be False once all currently readable
    log files have been read. It does not mean that no new logs will be written in the future.
    """

    log_key: Sequence[str]
    line: int  # maybe rename line_offset?
    has_more_now: bool

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        raw = json.dumps(
            {"log_key": self.log_key, "line": self.line, "has_more_now": self.has_more_now}
        )
        return base64.b64encode(bytes(raw, encoding="utf-8")).decode("utf-8")

    @staticmethod
    def parse(cursor_str: str) -> "LogLineCursor":
        raw = json.loads(base64.b64decode(cursor_str).decode("utf-8"))
        return LogLineCursor(raw["log_key"], raw["line"], raw["has_more_now"])
