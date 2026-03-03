import subprocess

import pytest
from dagster._utils import file_relative_path
from dagster_shared.seven import IS_WINDOWS


@pytest.mark.skipif(IS_WINDOWS, reason="fails on windows, unix coverage sufficient")
def test_sling_not_imported_on_dagster_sling_import():
    """Verify that the sling package is not imported when importing dagster-sling.

    The sling package has expensive side effects on import, including potentially
    downloading binaries from the internet. We defer the import so users don't
    pay this cost unless they're actually running code that requires sling.
    """
    py_file = file_relative_path(__file__, "simple_import.py")

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

    import_profile_lines = import_profile.split("\n")
    import_names = [line.split("|")[-1].strip() for line in import_profile_lines]

    # The sling package should NOT be imported when just importing dagster-sling
    # because we defer the import until actual sling operations are performed
    sling_imports = [name for name in import_names if name == "sling" or name.startswith("sling.")]

    assert not sling_imports, (
        "The `sling` package was imported when importing `dagster-sling`, "
        "but it should be deferred to avoid expensive side effects on import. "
        f"Found sling imports: {sling_imports}; to debug, "
        "`pip install tuna`, then run "
        "`python -X importtime python_modules/libraries/dagster-sling/dagster_sling_tests/import_perf_tests/simple_import.py &> /tmp/import.txt && tuna /tmp/import.txt`."
    )
