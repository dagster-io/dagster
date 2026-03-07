import subprocess
import sys

from dagster import file_relative_path


def test_sling_import_perf():
    py_file = file_relative_path(__file__, "simple_import.py")

    # import cost profiling output in stderr via "-X importtime"
    result = subprocess.run(
        [
            sys.executable,
            "-X",
            "importtime",
            py_file,
        ],
        check=True,
        capture_output=True,
    )
    import_profile = result.stderr.decode("utf-8")

    import_profile_lines = import_profile.split("\n")
    import_names = [line.split("|")[-1].strip() for line in import_profile_lines]

    # ensure expensive libraries which should not be needed for basic definitions are not imported
    # sling has side effects on import (downloading binaries) so we want to defer its import
    expensive_libraries = [
        "sling",
    ]
    expensive_imports = [
        f"`{lib}`"
        for lib in expensive_libraries
        if any(import_name.startswith(lib) for import_name in import_names)
    ]

    # if `tuna` output is unfriendly, another way to debug imports is to open `/tmp/import.txt`
    # using https://kmichel.github.io/python-importtime-graph/
    assert not expensive_imports, (
        "The following expensive libraries were imported with the top-level `dagster-sling` module: "
        f"{', '.join(expensive_imports)}; to debug, "
        "`pip install tuna`, then run "
        "`python -X importtime python_modules/libraries/dagster-sling/dagster_sling_tests/perf_tests/simple_import.py &> /tmp/import.txt && tuna /tmp/import.txt`."
    )
