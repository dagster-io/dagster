import subprocess

import pytest
from dagster._seven import IS_WINDOWS
from dagster._utils import file_relative_path


@pytest.mark.skipif(IS_WINDOWS, reason="fails on windows, unix coverage sufficient")
def test_import_perf():
    py_file = file_relative_path(__file__, "simple.py")

    # import cost profiling output in stderr via "-X importtime"
    result = subprocess.run(
        [
            "python",
            "-X",
            "importtime",
            py_file,
        ],
        check=True,
        capture_output=True,
    )
    import_profile = result.stderr.decode("utf-8")

    # ensure expensive libraries which should not be needed for basic definitions are not imported
    expensive_library = [
        "grpc",
        "sqlalchemy",
        "upath.",  # don't conflate with import of upath_io_manager
    ]
    expensive_imports = [f"`{lib}`" for lib in expensive_library if lib in import_profile]

    # if `tuna` output is unfriendly, another way to debug imports is to open `/tmp/import.txt`
    # using https://kmichel.github.io/python-importtime-graph/
    assert not expensive_imports, (
        "The following expensive libraries were imported with the top-level `dagster` module, "
        f"slowing down any process that imports Dagster: {', '.join(expensive_imports)}; to debug, "
        "`pip install tuna`, then run "
        "`python -X importtime python_modules/dagster/dagster_tests/general_tests/simple.py &> /tmp/import.txt && tuna /tmp/import.txt`."
    )
