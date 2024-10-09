import pytest
from dagster._core.definitions.utils import MAX_TITLE_LENGTH, check_valid_title, is_valid_title
from dagster._core.errors import DagsterInvariantViolationError
from dagster._utils.tags import is_valid_strict_tag_value, is_valid_tag_key


def test_is_valid_definition_tag_key_kinds() -> None:
    assert is_valid_tag_key("dagster/kind/foo") is True
    assert is_valid_tag_key("dagster/kind/foo.bar") is True
    assert is_valid_tag_key("dagster/kind/") is False
    assert is_valid_tag_key("dagster/kind/" + "a" * 63) is True

    assert is_valid_tag_key("dragster/kind/foo") is False


def test_is_valid_definition_tag_key():
    assert is_valid_tag_key("abc") is True
    assert is_valid_tag_key("abc.xhz") is True
    assert is_valid_tag_key("abc-xhz") is True
    assert is_valid_tag_key("abc/xyz") is True
    assert is_valid_tag_key("afdjkl.fdskj.-fsdj_lk") is True
    assert is_valid_tag_key("abc/xyz/fdjks") is False
    assert is_valid_tag_key("/xyzfdjks") is False
    assert is_valid_tag_key("xyzfdjks/") is False
    assert is_valid_tag_key("") is False
    assert is_valid_tag_key("a" * 63) is True
    assert is_valid_tag_key("a" * 64) is False
    assert is_valid_tag_key("a" * 63 + "/" + "b" * 63) is True
    assert is_valid_tag_key("a" * 64 + "/" + "b" * 63) is False


def test_is_valid_definition_tag_value():
    assert is_valid_strict_tag_value("abc") is True
    assert is_valid_strict_tag_value("abc.xhz") is True
    assert is_valid_strict_tag_value("abc-xhz") is True
    assert is_valid_strict_tag_value("abc/xyz") is False
    assert is_valid_strict_tag_value("afdjkl.fdskj.-fsdj_lk") is True
    assert is_valid_strict_tag_value("abc/xyz/fdjks") is False
    assert is_valid_strict_tag_value("/xyzfdjks") is False
    assert is_valid_strict_tag_value("xyzfdjks/") is False
    assert is_valid_strict_tag_value("") is True
    assert is_valid_strict_tag_value("a" * 63) is True
    assert is_valid_strict_tag_value("a" * 64) is False
    assert is_valid_strict_tag_value("a" * 63 + "/" + "b" * 63) is False
    assert is_valid_strict_tag_value("a" * 64 + "/" + "b" * 63) is False


def test_is_valid_title():
    assert is_valid_title("this is a valid title")
    assert is_valid_title("This is ALSO a valid title 12345")
    assert not is_valid_title("no astricks *")
    assert not is_valid_title("no precentage symbols %")
    assert not is_valid_title('no " quotes')
    assert is_valid_title("other symbols are ok @$#!?&|")

    with pytest.raises(DagsterInvariantViolationError, match="Titles must not contain regex"):
        check_valid_title("no astricks *")

    with pytest.raises(DagsterInvariantViolationError, match="Titles must not be longer than"):
        check_valid_title("a" * (MAX_TITLE_LENGTH + 1))
