'''Spark config codegen.

This script parses the Spark configuration parameters downloaded from the Spark Github repository,
and codegens a file that contains dagster configurations for these parameters.
'''
import re

import requests
import pytablereader as ptr

from six import StringIO

from dagster.utils.indenting_printer import IndentingPrinter


SPARK_VERSION = "v2.4.0"
TABLE_REGEX = r"### (.{,20}?)\n\n(<table.*?>.*?<\/table>)"


class IndentingBufferPrinter(IndentingPrinter):
    '''Subclass of IndentingPrinter wrapping a StringIO.'''

    def __init__(self, indent_level=4, current_indent=0):
        self.buffer = StringIO()
        self.printer = lambda x: self.buffer.write(x + '\n')
        super(IndentingBufferPrinter, self).__init__(
            indent_level=indent_level, printer=self.printer, current_indent=current_indent
        )

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self.buffer.close()

    def read(self):
        '''Get the value of the backing StringIO.'''
        return self.buffer.getvalue()


class SparkConfig:
    def __init__(self, path, default, meaning):
        self.path = path

        # The original documentation strings include extraneous newlines, spaces
        WHITESPACE_REGEX = r'\s+'
        self.default = re.sub(WHITESPACE_REGEX, ' ', str(default)).strip()
        self.meaning = re.sub(WHITESPACE_REGEX, ' ', meaning).strip()

    @property
    def split_path(self):
        return self.path.split('.')

    @property
    def path_length(self):
        return len(self.split_path)

    def __repr__(self):
        return 'SparkConfig(%s)' % self.path

    def print(self, printer):
        printer.append('Field(')
        with printer.with_indent():
            printer.line('')
            printer.line('String,')
            printer.append("description='''")
            printer.append(self.meaning)
            printer.line("''',")
            # printer.line("default_value='{}',".format(self.default))
        printer.append(')')


class SparkConfigNode:
    def __init__(self, value=None):
        self.value = value
        self.children = {}

    def print(self, printer):
        if not self.children:
            self.value.print(printer)
        else:
            if self.value:
                retdict = {'root': self.value}
                retdict.update(self.children)
            else:
                retdict = self.children

            printer.append('Field(')
            printer.line('')
            with printer.with_indent():
                printer.line('PermissiveDict(')
                with printer.with_indent():
                    printer.line('fields={')
                    with printer.with_indent():
                        for i, (k, v) in enumerate(retdict.items()):
                            with printer.with_indent():
                                printer.append("'{}': ".format(k))
                            v.print(printer)

                            printer.line(',')
                    printer.line('}')
                printer.line(')')
            printer.line(')')
        return printer.read()


def main():
    r = requests.get(
        'https://raw.githubusercontent.com/apache/spark/{}/docs/configuration.md'.format(
            SPARK_VERSION
        )
    )

    tables = re.findall(TABLE_REGEX, r.text, re.DOTALL | re.MULTILINE)

    spark_configs = []
    for name, table in tables:
        parsed_table = list(ptr.HtmlTableTextLoader(table).load())[0]
        df = parsed_table.as_dataframe()
        for _, row in df.iterrows():
            s = SparkConfig(row['Property Name'], row['Default'], name + ": " + row['Meaning'])
            spark_configs.append(s)

    result = SparkConfigNode()
    for s in spark_configs:
        key_path = s.split_path
        d = result
        while key_path:
            key = key_path.pop(0)
            if key not in d.children:
                d.children[key] = SparkConfigNode()
            d = d.children[key]
        d.value = s

    with IndentingBufferPrinter() as printer:
        printer.line("'''NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT")
        printer.blank_line()
        printer.line("'''")
        printer.blank_line()
        printer.blank_line()
        printer.line('from dagster import Field, PermissiveDict, String')
        printer.blank_line()
        printer.blank_line()
        printer.line('def spark_config():')
        with printer.with_indent():
            printer.append('return ')
            result.print(printer)
            print(printer.read())


if __name__ == "__main__":
    main()
