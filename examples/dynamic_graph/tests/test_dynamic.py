from dagster import execute_pipeline

from ..repo import process_directory


def test_fan_in_pipeline():
    result = execute_pipeline(process_directory)
    assert result.success

    assert result.result_for_solid("process_file").output_value() == {
        "empty_stuff_bin": 0,
        "program_py": 34,
        "words_txt": 40,
    }
