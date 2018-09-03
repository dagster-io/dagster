import pytest

from dagster.utils.indenting_printer import IndentingPrinter


class CollectingIndentingPrinter(IndentingPrinter):
    def __init__(self, *args, **kwargs):
        self.lines = []

        def _add_line(text):
            if str is not None:
                self.lines.append(text)

        super(CollectingIndentingPrinter, self).__init__(printer=_add_line, *args, **kwargs)

    def result(self):
        return '\n'.join(self.lines)


def create_printer(*args, **kwargs):
    return CollectingIndentingPrinter(*args, **kwargs)


def test_basic_printer():
    printer = create_printer()
    printer.line('test')

    assert printer.result() == 'test'


def test_indent_printer():
    printer = create_printer()
    printer.line('test')
    with printer.with_indent():
        printer.line('test indent')

    assert printer.result() == '''test
  test indent'''


def test_parameterized_indent():
    printer = create_printer(indent_level=4)
    printer.line('test')
    with printer.with_indent():
        printer.line('test indent')

    assert printer.result() == '''test
    test indent'''


def test_bad_decrease_indent():
    printer = create_printer(indent_level=4)
    with pytest.raises(Exception):
        printer.decrease_indent()


def test_indent_printer_blank_line():
    printer = create_printer()
    printer.line('test')
    printer.blank_line()
    with printer.with_indent():
        printer.line('test indent')

    assert printer.result() == '''test

  test indent'''


def test_double_indent():
    printer = create_printer()
    printer.line('test')
    with printer.with_indent():
        printer.line('test indent')
        with printer.with_indent():
            printer.line('test double indent')

    assert printer.result() == '''test
  test indent
    test double indent'''
