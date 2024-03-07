from dagster._core.definitions.utils import (
    is_valid_definition_tag_key,
    is_valid_definition_tag_value,
)


def test_is_valid_definition_tag_key():
    assert is_valid_definition_tag_key("abc") is True
    assert is_valid_definition_tag_key("abc.xhz") is True
    assert is_valid_definition_tag_key("abc-xhz") is True
    assert is_valid_definition_tag_key("abc/xyz") is True
    assert is_valid_definition_tag_key("afdjkl.fdskj.-fsdj_lk") is True
    assert is_valid_definition_tag_key("abc/xyz/fdjks") is False
    assert is_valid_definition_tag_key("/xyzfdjks") is False
    assert is_valid_definition_tag_key("xyzfdjks/") is False
    assert is_valid_definition_tag_key("") is False
    assert is_valid_definition_tag_key("a" * 63) is True
    assert is_valid_definition_tag_key("a" * 64) is False
    assert is_valid_definition_tag_key("a" * 63 + "/" + "b" * 63) is True
    assert is_valid_definition_tag_key("a" * 64 + "/" + "b" * 63) is False


def test_is_valid_definition_tag_value():
    assert is_valid_definition_tag_value("abc") is True
    assert is_valid_definition_tag_value("abc.xhz") is True
    assert is_valid_definition_tag_value("abc-xhz") is True
    assert is_valid_definition_tag_value("abc/xyz") is False
    assert is_valid_definition_tag_value("afdjkl.fdskj.-fsdj_lk") is True
    assert is_valid_definition_tag_value("abc/xyz/fdjks") is False
    assert is_valid_definition_tag_value("/xyzfdjks") is False
    assert is_valid_definition_tag_value("xyzfdjks/") is False
    assert is_valid_definition_tag_value("") is True
    assert is_valid_definition_tag_value("a" * 63) is True
    assert is_valid_definition_tag_value("a" * 64) is False
    assert is_valid_definition_tag_value("a" * 63 + "/" + "b" * 63) is False
    assert is_valid_definition_tag_value("a" * 64 + "/" + "b" * 63) is False
