import dagster as dg
from dagster._utils import safe_isfile


def test_safe_isfile():
    assert safe_isfile(dg.file_relative_path(__file__, "test_file_utils.py"))
    assert not safe_isfile(dg.file_relative_path(__file__, "not_a_file.py"))


def test_script_relative_path_file_relative_path_equiv():
    assert dg.file_relative_path(__file__, "foo") == dg.file_relative_path(__file__, "foo")
