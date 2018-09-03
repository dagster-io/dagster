from __future__ import print_function
from contextlib import contextmanager

from dagster import check


class IndentingPrinter(object):
    def __init__(self, indent_level=2, printer=print):
        self.lines = []
        self.current_indent = 0
        self.indent_level = check.int_param(indent_level, 'indent_level')
        self.printer = check.callable_param(printer, 'printer')

    def line(self, text):
        check.str_param(text, 'text')
        self.printer(self.current_indent_str + text)

    @property
    def current_indent_str(self):
        return ' ' * self.current_indent

    def blank_line(self):
        self.printer('')

    def increase_indent(self):
        self.current_indent += self.indent_level

    def decrease_indent(self):
        if self.current_indent <= 0:
            raise Exception('indent cannot be negative')
        self.current_indent -= self.indent_level

    @contextmanager
    def with_indent(self, text=None):
        if text is not None:
            self.line(text)
        self.increase_indent()
        yield
        self.decrease_indent()
