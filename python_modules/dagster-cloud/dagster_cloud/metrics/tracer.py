import base64
import json
import time
from contextlib import contextmanager

# A minimal copy of the standard OTEL API


class Span:
    def __init__(self, name: str):
        self._name = name
        self._attrs = {}
        self._start_time = time.time()
        self._end_time = None

    def set_attribute(self, key: str, value: int | str):
        self._attrs[key] = value

    def end(self):
        self._end_time = time.time()

    def get_serialized(self) -> str:
        # base64 to make it safe for a http header (no newlines, few special chars)
        return base64.b64encode(
            json.dumps(
                {
                    "_name": self._name,
                    "_duration": self._end_time - self._start_time
                    if self._end_time is not None
                    else None,
                    **self._attrs,
                },
                separators=(",", ":"),
                indent=None,
            ).encode("utf-8")
        ).decode()


class Tracer:
    def __init__(self):
        self._spans: list[Span] = []

    @contextmanager
    def start_span(self, name: str):
        span = Span(name)
        try:
            yield span
        finally:
            span.end()
            self._spans.append(span)

    def pop_serialized_span(self) -> str | None:
        try:
            span = self._spans.pop(0)
        except IndexError:
            return None
        else:
            return span.get_serialized()
