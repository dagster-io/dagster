import pytest
from dagster.check import CheckError
from dagster.utils.indenting_printer import IndentingPrinter, IndentingStringIoPrinter

LOREM_IPSUM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut "
    "labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco "
    "laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in "
    "voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat "
    "cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum"
)

FORMATTED_LOREM = """# Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut
# labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris
# nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit
# esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt
# in culpa qui officia deserunt mollit anim id est laborum
    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut
    labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco
    laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in
    voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat
    non proident, sunt in culpa qui officia deserunt mollit anim id est laborum
        # Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
        # ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
        # ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
        # reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur
        # sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id
        # est laborum
"""


class CollectingIndentingPrinter(IndentingPrinter):
    def __init__(self, *args, **kwargs):
        self.lines = []

        def _add_line(text):
            if str is not None:
                self.lines.append(text)

        super(CollectingIndentingPrinter, self).__init__(printer=_add_line, *args, **kwargs)

    def result(self):
        return "\n".join(self.lines)


def create_printer(*args, **kwargs):
    return CollectingIndentingPrinter(*args, **kwargs)


def test_basic_printer():
    printer = create_printer()
    printer.line("test")

    assert printer.result() == "test"


def test_indent_printer():
    printer = create_printer()
    printer.line("test")
    with printer.with_indent():
        printer.line("test indent")
    with printer.with_indent("bop"):
        printer.line("another")
        printer.line("yet")

    assert printer.result() == ("test\n" "  test indent\n" "bop\n" "  another\n" "  yet")


def test_parameterized_indent():
    printer = create_printer(indent_level=4)
    printer.line("test")
    with printer.with_indent():
        printer.line("test indent")

    assert (
        printer.result()
        == """test
    test indent"""
    )


def test_bad_decrease_indent():
    printer = create_printer(indent_level=4)
    with pytest.raises(Exception):
        printer.decrease_indent()


def test_indent_printer_blank_line():
    printer = create_printer()
    printer.line("test")
    printer.blank_line()
    with printer.with_indent():
        printer.line("test indent")

    assert (
        printer.result()
        == """test

  test indent"""
    )


def test_double_indent():
    printer = create_printer()
    printer.line("test")
    with printer.with_indent():
        printer.line("test indent")
        with printer.with_indent():
            printer.line("test double indent")

    assert (
        printer.result()
        == """test
  test indent
    test double indent"""
    )


def test_append():
    printer = create_printer()
    printer.append("a")
    printer.line("")

    assert printer.result() == "a"


def test_double_append():
    printer = create_printer()
    printer.append("a")
    printer.append("a")
    printer.line("")

    assert printer.result() == "aa"


def test_append_plus_line():
    printer = create_printer()
    printer.append("a")
    printer.line("b")

    assert printer.result() == "ab"


def test_blank_line_error():
    with pytest.raises(CheckError):
        printer = create_printer()
        printer.append("a")
        printer.blank_line()


def test_indenting_block_printer_context_management():
    with IndentingStringIoPrinter() as printer:
        printer.line("Hello, world!")
        assert printer.read() == "Hello, world!\n"


def test_indenting_block_printer_block_printing():
    with IndentingStringIoPrinter(indent_level=4) as printer:
        printer.comment(LOREM_IPSUM)
        with printer.with_indent():
            printer.block(LOREM_IPSUM)
            with printer.with_indent():
                printer.comment(LOREM_IPSUM)
        assert printer.read() == FORMATTED_LOREM
