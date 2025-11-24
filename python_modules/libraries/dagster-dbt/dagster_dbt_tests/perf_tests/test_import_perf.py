import subprocess

from dagster import file_relative_path


def test_dbt_import_perf():
    py_file = file_relative_path(__file__, "simple_import.py")

    # import cost profiling output in stderr via "-X importtime"
    result = subprocess.run(
        [
            "python",
            "-X",
            "importtime",
            py_file,
            "noop",
        ],
        check=True,
        capture_output=True,
    )
    import_profile = result.stderr.decode("utf-8")

    import_profile_lines = import_profile.split("\n")
    import_names = [line.split("|")[-1].strip() for line in import_profile_lines]

    # ensure expensive libraries which should not be needed for basic definitions are not imported
    expensive_library = [
        "git",  # also has side effects on import
    ]
    expensive_imports = [
        f"`{lib}`"
        for lib in expensive_library
        if any(import_name.startswith(lib) for import_name in import_names)
    ]

    # if `tuna` output is unfriendly, another way to debug imports is to open `/tmp/import.txt`
    # using https://kmichel.github.io/python-importtime-graph/
    assert not expensive_imports, (
        "The following expensive libraries were imported with the top-level `dagster-dbt` module:"
        f"{', '.join(expensive_imports)}; to debug, "
        "`pip install tuna`, then run "
        "`python -X importtime python_modules/libraries/dagster-dbt/dagster_dbt_tests/perf_tests/simple_import.py noop &> /tmp/import.txt && tuna /tmp/import.txt`."
    )
