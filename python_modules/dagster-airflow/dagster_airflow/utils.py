'''Utilities to support dagster-airflow'''

from textwrap import TextWrapper

from six import StringIO

from dagster.utils.indenting_printer import IndentingPrinter


LINE_LENGTH = 100


class IndentingBlockPrinter(IndentingPrinter):
    '''Subclass of IndentingPrinter wrapping a StringIO.'''

    def __init__(self, line_length=LINE_LENGTH, indent_level=4, current_indent=0):
        self.buffer = StringIO()
        self.line_length = line_length
        self.printer = lambda x: self.buffer.write(x + '\n')
        super(IndentingBlockPrinter, self).__init__(
            indent_level=indent_level, printer=self.printer, current_indent=current_indent
        )

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self.buffer.close()

    def block(self, text, prefix=''):
        '''Automagically wrap a block of text.'''
        wrapper = TextWrapper(
            width=self.line_length - len(self.current_indent_str),
            initial_indent=prefix,
            subsequent_indent=prefix,
            break_long_words=False,
            break_on_hyphens=False,
        )
        for line in wrapper.wrap(text):
            self.line(line)

    def comment(self, text):
        self.block(text, prefix='# ')

    def read(self):
        '''Get the value of the backing StringIO.'''
        return self.buffer.getvalue()
