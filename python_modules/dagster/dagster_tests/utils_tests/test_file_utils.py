from dagster.utils import file_relative_path, safe_isfile, script_relative_path


def test_safe_isfile():
    assert safe_isfile(script_relative_path('test_file_utils.py'))
    assert not safe_isfile(script_relative_path('not_a_file.py'))


def test_script_relative_path_file_relative_path_equiv():
    assert script_relative_path('foo') == file_relative_path(__file__, 'foo')
