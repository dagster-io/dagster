import os
import sys
from io import StringIO
from typing import Any, Callable, List, Type

from dagster._utils.indenting_printer import IndentingPrinter


class IndentingBufferPrinter(IndentingPrinter):
    """Subclass of IndentingPrinter wrapping a StringIO."""

    buffer: StringIO

    def __init__(self, indent_level: int = 4, current_indent: int = 0):
        self.buffer = StringIO()
        self.printer: Callable[[str], Any] = lambda x: self.buffer.write(x + "\n")
        super(IndentingBufferPrinter, self).__init__(
            indent_level=indent_level, printer=self.printer, current_indent=current_indent
        )

    def __enter__(self) -> "IndentingBufferPrinter":
        return self

    def __exit__(
        self,
        _exception_type: Type[BaseException],
        _exception_value: BaseException,
        _traceback: List[str],
    ) -> None:
        self.buffer.close()

    def read(self) -> str:
        """Get the value of the backing StringIO."""
        return self.buffer.getvalue()

    def write_header(self) -> None:
        args = [os.path.basename(sys.argv[0])] + sys.argv[1:]
        self.line("'''NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT")
        self.blank_line()
        self.line("@generated")
        self.blank_line()
        self.line("Produced via:")
        self.line("\n\t".join("%s \\" % s for s in args if s != "--snapshot-update"))
        self.blank_line()
        self.line("'''")
        self.blank_line()
        self.blank_line()
