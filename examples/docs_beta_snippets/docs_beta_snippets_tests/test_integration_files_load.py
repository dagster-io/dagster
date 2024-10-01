import importlib.util
import os

import pytest

from dagster import file_relative_path

snippets_folder = file_relative_path(__file__, "../docs_beta_snippets/integrations")

EXCLUDED_FILES = {
    # exclude community integrations because they require non-editable dagster depdendencies
    f"{snippets_folder}/cube.py",
    f"{snippets_folder}/hightouch.py",
    f"{snippets_folder}/hashicorp.py",
    f"{snippets_folder}/meltano.py",
    f"{snippets_folder}/lakefs.py",
    # FIXME: need to enable the following once we have a way to run their init/compile script in CI
    f"{snippets_folder}/dbt.py",
    f"{snippets_folder}/sdf.py",
    f"{snippets_folder}/airbyte.py",
    f"{snippets_folder}/dlt.py",
    f"{snippets_folder}/fivetran.py",
    # FIXME: this breaks on py3.8 and seems related to the non-dagster dependencies
    f"{snippets_folder}/pandera.py",
}


def get_python_files(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                yield os.path.join(root, file)


@pytest.mark.parametrize("file_path", get_python_files(snippets_folder))
def test_file_loads(file_path):
    if file_path in EXCLUDED_FILES:
        pytest.skip(f"Skipped {file_path}")
        return
    spec = importlib.util.spec_from_file_location("module", file_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        pytest.fail(f"Failed to load {file_path}: {e!s}")
