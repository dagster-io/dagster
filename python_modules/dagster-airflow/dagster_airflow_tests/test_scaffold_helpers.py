import pytest

from dagster import check

from dagster.utils import script_relative_path

from dagster_airflow.scaffold import (
    _bad_import,
    format_config_for_graphql,
    _is_py,
    _normalize_key,
    _split_lines,
)


def test_normalize_key():
    assert _normalize_key('foo.bar_baz') == 'foo_bar__baz'


def test_is_py():
    assert _is_py(script_relative_path('test_scaffold_helpers.py'))
    assert not _is_py(script_relative_path('test_scaffold_helpers'))


def test_bad_import():
    assert not _bad_import('foo_bar.py')
    assert _bad_import('foo.bar.py')


def test_split_lines():
    assert _split_lines('foo\nbar\n') == ['foo', 'bar,']


def test_format_config():
    with pytest.raises(check.CheckError):
        format_config_for_graphql('')

    with pytest.raises(check.CheckError):
        format_config_for_graphql(None)

    with pytest.raises(check.CheckError):
        format_config_for_graphql([])

    with pytest.raises(check.CheckError):
        format_config_for_graphql(3)

    assert format_config_for_graphql({}) == '{\n}\n'

    assert format_config_for_graphql({'foo': 'bar'}) == '{\n  foo: "bar"\n}\n'

    assert (
        format_config_for_graphql({'foo': 'bar', 'baz': 'quux'})
        == '{\n  baz: "quux",\n  foo: "bar"\n}\n'
    )

    assert format_config_for_graphql({'foo': {'bar': 'baz', 'quux': 'bip'}}) == (
        '{\n' '  foo: {\n' '    bar: "baz",\n' '    quux: "bip"\n' '  }\n' '}\n'
    )

    assert format_config_for_graphql({'foo': {'bar': 3, 'quux': 'bip'}}) == (
        '{\n' '  foo: {\n' '    bar: 3,\n' '    quux: "bip"\n' '  }\n' '}\n'
    )

    assert format_config_for_graphql({'foo': {'bar': {'baz': {'quux': 'bip', 'bop': 'boop'}}}}) == (
        '{\n'
        '  foo: {\n'
        '    bar: {\n'
        '      baz: {\n'
        '        bop: "boop",\n'
        '        quux: "bip"\n'
        '      }\n'
        '    }\n'
        '  }\n'
        '}\n'
    )

    assert format_config_for_graphql({'foo': {'bar': ['baz', 'quux']}}) == (
        '{\n' '  foo: {\n' '    bar: [\n' '      "baz",\n' '      "quux"\n' '    ]\n' '  }\n' '}\n'
    )

    assert format_config_for_graphql({'foo': {'bar': ['baz', {'quux': 'ruux'}]}}) == (
        '{\n'
        '  foo: {\n'
        '    bar: [\n'
        '      "baz",\n'
        '      {\n'
        '        quux: "ruux"\n'
        '      }\n'
        '    ]\n'
        '  }\n'
        '}\n'
    )
