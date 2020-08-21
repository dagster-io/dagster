from dagster.utils import file_relative_path, safe_isfile


def test_safe_isfile():
    assert safe_isfile(file_relative_path(__file__, "test_file_utils.py"))
    assert not safe_isfile(file_relative_path(__file__, "not_a_file.py"))


def test_script_relative_path_file_relative_path_equiv():
    assert file_relative_path(__file__, "foo") == file_relative_path(__file__, "foo")
