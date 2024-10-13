from automation.printer import IndentingBufferPrinter


def test_header():
    with IndentingBufferPrinter() as printer:
        printer.write_header()
        result = printer.read()

    assert result.startswith(
        """'''NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT

@generated

Produced via:"""
    )


def test_rest():
    with IndentingBufferPrinter() as printer:
        printer.line("foo bar")
        printer.blank_line()
        printer.comment("this is a comment")
        with printer.with_indent():
            printer.line("indented")
        result = printer.read()
    assert (
        result
        == """foo bar

# this is a comment
    indented
"""
    )


def test_block():
    with IndentingBufferPrinter() as printer:
        printer.comment("this is a long string " * 10)
        result = printer.read()
    assert (
        result
        == """# this is a long string this is a long string this is a long string this is a long"""
        """ string this is a\n"""
        """# long string this is a long string this is a long string this is a long string this"""
        """ is a long\n# string this is a long string\n"""
    )
