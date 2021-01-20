from contextlib import contextmanager
from io import StringIO
from textwrap import TextWrapper

from dagster import check

LINE_LENGTH = 100


class IndentingPrinter:
    def __init__(self, indent_level=2, printer=print, current_indent=0, line_length=LINE_LENGTH):
        self.current_indent = current_indent
        self.indent_level = check.int_param(indent_level, "indent_level")
        self.printer = check.callable_param(printer, "printer")
        self.line_length = line_length

        self._line_so_far = ""

    def append(self, text):
        check.str_param(text, "text")
        self._line_so_far += text

    def line(self, text):
        check.str_param(text, "text")
        self.printer(self.current_indent_str + self._line_so_far + text)
        self._line_so_far = ""

    def block(self, text, prefix="", initial_indent=""):
        """Automagically wrap a block of text."""
        wrapper = TextWrapper(
            width=self.line_length - len(self.current_indent_str),
            initial_indent=initial_indent,
            subsequent_indent=prefix,
            break_long_words=False,
            break_on_hyphens=False,
        )
        for line in wrapper.wrap(text):
            self.line(line)

    def comment(self, text):
        self.block(text, prefix="# ", initial_indent="# ")

    @property
    def current_indent_str(self):
        return " " * self.current_indent

    def blank_line(self):
        check.invariant(
            not self._line_so_far, "Cannot throw away appended strings by calling blank_line"
        )
        self.printer("")

    def increase_indent(self):
        self.current_indent += self.indent_level

    def decrease_indent(self):
        if self.indent_level and self.current_indent <= 0:
            raise Exception("indent cannot be negative")
        self.current_indent -= self.indent_level

    @contextmanager
    def with_indent(self, text=None):
        if text is not None:
            self.line(text)
        self.increase_indent()
        yield
        self.decrease_indent()


class IndentingStringIoPrinter(IndentingPrinter):
    """Subclass of IndentingPrinter wrapping a StringIO."""

    def __init__(self, **kwargs):
        self.buffer = StringIO()
        self.printer = lambda x: self.buffer.write(x + "\n")
        super(IndentingStringIoPrinter, self).__init__(printer=self.printer, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self.buffer.close()

    def read(self):
        """Get the value of the backing StringIO."""
        return self.buffer.getvalue()
