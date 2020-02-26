# encoding: utf-8

from __future__ import unicode_literals

import json
import tempfile

import pytest

from dagster import seven
from dagster.utils import file_relative_path


def test_is_ascii():
    assert seven.is_ascii('Hello!')
    assert not seven.is_ascii('您好！')


def test_import_module_from_path():
    foo_module = seven.import_module_from_path(
        'foo_module', file_relative_path(__file__, 'foo_module.py')
    )
    assert foo_module.FOO == 7


def test_json_decode_error():
    with pytest.raises(seven.json.JSONDecodeError):
        json.loads(',dsfjd')


def test_json_dump():
    with tempfile.TemporaryFile('w+') as fd:
        seven.json.dump({'foo': 'bar', 'a': 'b'}, fd)
        fd.seek(0)
        assert fd.read() == '{"a": "b", "foo": "bar"}'


def test_json_dumps():
    assert seven.json.dumps({'foo': 'bar', 'a': 'b'}) == '{"a": "b", "foo": "bar"}'


def test_tempdir():
    assert not seven.temp_dir.get_system_temp_directory().startswith('/var')


def test_get_args():
    def foo(one, two=2, three=None):  # pylint: disable=unused-argument
        pass

    assert len(seven.get_args(foo)) == 3
    assert 'one' in seven.get_args(foo)
    assert 'two' in seven.get_args(foo)
    assert 'three' in seven.get_args(foo)
