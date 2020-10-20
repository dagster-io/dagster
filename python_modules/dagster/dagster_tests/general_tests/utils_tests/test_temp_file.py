import pytest
from dagster.utils.temp_file import get_temp_file_name, get_temp_file_names


@pytest.mark.skipif('"win" in sys.platform', reason="resource module not available in windows")
def test_get_temp_file_name_leak_file_descriptors():
    import resource

    resource.setrlimit(resource.RLIMIT_NOFILE, (100, 100))
    for _ in range(100):
        with get_temp_file_name() as _:
            pass

    for _ in range(100):
        with get_temp_file_names(1) as _:
            pass
