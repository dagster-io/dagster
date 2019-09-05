import pytest

from dagster.core.selector import (
    NameToken,
    PlusToken,
    SelectionParserException,
    WhitespaceToken,
    has_valid_name_chars,
    parse_selector_text,
    tokenize_selector_text,
)


def test_plus_has_valid():
    assert not has_valid_name_chars('+')


def test_basic_selector_string():
    assert tokenize_selector_text('foo') == [NameToken(pos=0, name='foo')]


def test_basic_selector_plus_string():
    assert tokenize_selector_text('+foo') == [PlusToken(pos=0), NameToken(pos=1, name='foo')]
    assert tokenize_selector_text('foo+') == [NameToken(pos=0, name='foo'), PlusToken(pos=3)]


def test_basic_selector_comma_splice():
    assert tokenize_selector_text('foo bar') == [
        NameToken(pos=0, name='foo'),
        WhitespaceToken(pos=3),
        NameToken(pos=4, name='bar'),
    ]


def parse_single_selection(text):
    selections = parse_selector_text(text)
    assert len(selections) == 1
    return selections[0]


def test_parse_basic_selector():
    selection = parse_single_selection('foo')
    assert selection.name == 'foo'
    assert selection.include_upstream is False
    assert selection.include_downstream is False


def test_parse_basic_selector_pluses():
    up = parse_single_selection('+foo')
    assert up.name == 'foo'
    assert up.include_upstream is True
    assert up.include_downstream is False

    down = parse_single_selection('foo+')
    assert down.name == 'foo'
    assert down.include_upstream is False
    assert down.include_downstream is True

    both = parse_single_selection('+foo+')
    assert both.name == 'foo'
    assert both.include_upstream is True
    assert both.include_downstream is True


def test_invalid_char_error():
    with pytest.raises(SelectionParserException) as exc_info:
        parse_single_selection('<')

    assert str(exc_info.value) == "Invalid character '<' at char pos 0"


def test_double_plus():
    with pytest.raises(SelectionParserException) as exc_info:
        parse_single_selection('++foo')

    assert str(exc_info.value) == "Unexpected character '+' at pos 1. Expected solid name."


def test_dangling_plus():
    with pytest.raises(SelectionParserException) as exc_info:
        parse_single_selection('+')

    assert str(exc_info.value) == "Dangling plus character at pos 0"


def test_two_solids():
    selections = parse_selector_text('foo bar')

    assert len(selections) == 2

    foo_selection = selections[0]
    assert foo_selection.name == 'foo'
    assert foo_selection.include_upstream is False
    assert foo_selection.include_downstream is False

    bar_selection = selections[1]
    assert bar_selection.name == 'bar'
    assert bar_selection.include_upstream is False
    assert bar_selection.include_downstream is False


def test_solids_different_plus():
    selections = parse_selector_text('+up down+ +both+ neither')

    assert len(selections) == 4

    up_selection = selections[0]
    assert up_selection.name == 'up'
    assert up_selection.include_upstream is True
    assert up_selection.include_downstream is False

    down_selection = selections[1]
    assert down_selection.name == 'down'
    assert down_selection.include_upstream is False
    assert down_selection.include_downstream is True

    both_selection = selections[2]
    assert both_selection.name == 'both'
    assert both_selection.include_upstream is True
    assert both_selection.include_downstream is True

    neither_selection = selections[3]
    assert neither_selection.name == 'neither'
    assert neither_selection.include_upstream is False
    assert neither_selection.include_downstream is False
