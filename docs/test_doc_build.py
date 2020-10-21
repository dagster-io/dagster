import json
import os
import subprocess

import pytest
import six

from dagster import check
from dagster.utils import file_relative_path


def git_repo_root():
    return six.ensure_str(subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).strip())


def assert_documented_exports(module_name, module, whitelist=None):
    whitelist = check.opt_set_param(whitelist, "whitelist")

    all_exports = module.__all__
    path_to_export_index = os.path.join(git_repo_root(), "docs/next/src/data/exportindex.json")
    with open(path_to_export_index, "r") as f:
        export_index = json.load(f)
        documented_exports = set(export_index[module_name])
        undocumented_exports = set(all_exports).difference(documented_exports).difference(whitelist)
        assert len(undocumented_exports) == 0, "Top level exports {} are not documented".format(
            undocumented_exports
        )


def test_documented_exports():
    # If this test is failing, you have added a top level export to a module that is undocumented.
    # Make sure you include documentation for the new export in the appropriate file under
    # docs/sections/api/apidocs and add a docblock to the definition.

    import dagster
    import dagster_gcp
    import dagster_pandas

    modules = {
        "dagster": {
            "module": dagster,
            "whitelist": {
                # NOTE: Do not add any additional entries to this whitelist
                "RetryRequested",
                "ScalarUnion",
                "DefaultRunLauncher",
                "build_intermediate_storage_from_object_store",
                "SolidExecutionContext",
                "SerializationStrategy",
                "Materialization",
                "local_file_manager",
                "SystemStorageData",
                "PipelineRun",
            },
        },
        "dagster_gcp": {"module": dagster_gcp},
        "dagster_pandas": {
            "module": dagster_pandas,
            "whitelist": {
                # NOTE: Do not add any additional entries to this whitelist
                "ConstraintWithMetadataException",
                "all_unique_validator",
                "ColumnWithMetadataException",
                "categorical_column_validator_factory",
                "MultiConstraintWithMetadata",
                "MultiColumnConstraintWithMetadata",
                "non_null_validation",
                "StrictColumnsWithMetadata",
                "MultiAggregateConstraintWithMetadata",
                "ConstraintWithMetadata",
                "dtype_in_set_validation_factory",
                "nonnull",
                "create_structured_dataframe_type",
                "column_range_validation_factory",
            },
        },
    }

    for module_name, value in modules.items():
        module = value["module"]
        whitelist = value.get("whitelist")
        assert_documented_exports(module_name, module, whitelist)


@pytest.mark.docs
def test_build_all_docs():
    pwd = os.getcwd()
    try:
        os.chdir(file_relative_path(__file__, "."))
        subprocess.check_output(["make", "clean"])
        subprocess.check_output(["make", "html"])
    finally:
        os.chdir(pwd)
