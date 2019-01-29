from dagster_airflow.utils import IndentingBlockPrinter

LOREM_IPSUM = (
    'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut '
    'labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco '
    'laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in '
    'voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat '
    'cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum'
)

FORMATTED_LOREM = \
'''# Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut
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
'''

def test_indenting_block_printer_context_management():
    with IndentingBlockPrinter() as printer:
        printer.line('Hello, world!')
        assert printer.read() == 'Hello, world!\n'


def test_indenting_block_printer_block_printing():
    with IndentingBlockPrinter() as printer:
        printer.comment(LOREM_IPSUM)
        with printer.with_indent():
            printer.block(LOREM_IPSUM)
            with printer.with_indent():
                printer.comment(LOREM_IPSUM)
        assert printer.read() == FORMATTED_LOREM
