from dagster.utils import safe_isfile, script_relative_path


def test_safe_isfile():
    assert safe_isfile(script_relative_path('test_safe_isfile.py'))
    assert not safe_isfile(script_relative_path('test_safe_isfile_foobar.py'))
