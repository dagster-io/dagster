import subprocess

import pytest
from dagster._utils import file_relative_path
from dagster_shared.seven import IS_WINDOWS


@pytest.mark.skipif(IS_WINDOWS, reason="fails on windows, unix coverage sufficient")
def test_import_perf():
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
        "grpc",
        "sqlalchemy",
        "upath.",  # don't conflate with import of upath_io_manager
        "structlog",
        "fsspec",
        "gql",
        "jinja2",
        "jsonschema",
        "requests",
        "dagster_shared.dagster_model",
        "dagster_cloud_cli.config",
        "urllib.request",
        "yaml",
        "typer",
        "http.server",
        "pydantic",
        "tomlkit",
        "watchdog",
        "dotenv",
        "claude_code_sdk",
    ]
    expensive_imports = [
        f"`{lib}`"
        for lib in expensive_library
        if any(import_name.startswith(lib) for import_name in import_names)
    ]

    # if `tuna` output is unfriendly, another way to debug imports is to open `/tmp/import.txt`
    # using https://kmichel.github.io/python-importtime-graph/
    assert not expensive_imports, (
        "The following expensive libraries were imported with the top-level `dagster_dg_cli` module, "
        f"slowing down any process that imports dg: {', '.join(expensive_imports)}; to debug, "
        "`pip install tuna`, then run "
        "`python -X importtime python_modules/libraries/dagster-dg-cli/dagster_dg_cli_tests/cli_tests/import_perf_tests/simple_import.py noop &> /tmp/import.txt && tuna /tmp/import.txt`."
    )
