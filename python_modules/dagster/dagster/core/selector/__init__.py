from collections import namedtuple

from dagster import check
from dagster.core.definitions.utils import has_valid_name_chars

PLUS_CHAR = '+'

PlusToken = namedtuple('PlusToken', 'pos')
WhitespaceToken = namedtuple('WhitespaceToken', 'pos')
NameToken = namedtuple('NameToken', 'pos name')

WHITESPACE_CHARS = {' ', '\t', '\r', '\n'}


class SelectionParserException(Exception):
    def __init__(self, message, pos, text):
        self.pos = check.int_param(pos, 'pos')
        self.text = check.str_param(text, 'text')
        super(SelectionParserException, self).__init__(message)


def parse_selector_text(text):
    return parse_tokens(tokenize_selector_text(text), text)


def tokenize_selector_text(text):

    check.str_param(text, 'text')

    pos = 0

    tokens = []

    while pos < len(text):
        ch = text[pos]
        if ch == PLUS_CHAR:
            tokens.append(PlusToken(pos=pos))
            pos += 1
        elif ch in WHITESPACE_CHARS:
            initial_pos = pos
            while pos < len(text) and text[pos] in WHITESPACE_CHARS:
                pos += 1

            tokens.append(WhitespaceToken(pos=initial_pos))
        elif has_valid_name_chars(ch):  # valid name
            new_name = ''
            initial_pos = pos
            while pos < len(text) and has_valid_name_chars(text[pos]):
                new_name += text[pos]
                pos += 1

            tokens.append(NameToken(pos=initial_pos, name=new_name))
        else:
            raise SelectionParserException(
                'Invalid character {ch} at char pos {pos}'.format(ch=repr(ch), pos=pos),
                pos=pos,
                text=text,
            )

    return tokens


Selection = namedtuple('Selection', 'name include_upstream include_downstream')


def parse_tokens(tokens, original_text):
    current_name = None
    index = 0
    selections = []
    while index < len(tokens):
        has_plus_prefix = False
        if isinstance(tokens[index], PlusToken):
            has_plus_prefix = True
            index += 1

        if index >= len(tokens):
            pos = tokens[index - 1].pos
            raise SelectionParserException(
                'Dangling plus character at pos {pos}'.format(pos=pos), pos=pos, text=original_text
            )

        if not isinstance(tokens[index], NameToken):
            pos = tokens[index].pos
            raise SelectionParserException(
                'Unexpected character {ch} at pos {pos}. Expected solid name.'.format(
                    ch=repr(original_text[pos]), pos=pos
                ),
                pos=pos,
                text=original_text,
            )

        current_name = tokens[index].name

        index += 1

        has_plus_suffix = False

        if index < len(tokens) and isinstance(tokens[index], PlusToken):
            has_plus_suffix = True
            index += 1

        selections.append(
            Selection(
                name=current_name,
                include_upstream=has_plus_prefix,
                include_downstream=has_plus_suffix,
            )
        )

        if index == len(tokens):
            break

        if not isinstance(tokens[index], WhitespaceToken):
            pos = tokens[index].pos
            raise SelectionParserException(
                'Unexpected character {ch} at pos {pos}. Expected whitespace.'.format(
                    ch=repr(original_text[pos]), pos=pos
                ),
                pos=pos,
                text=original_text,
            )

        index += 1

    return selections
