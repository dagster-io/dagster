import warnings

import pytest
from dagster import AssetExecutionContext, OpExecutionContext, asset, materialize
from dagster._core.execution.context.compute import _get_deprecation_kwargs

def test_doc_strings():
    ignores = [
        "_abc_impl",
        "_events",
        "_output_metadata",
        "_pdb",
        "_step_execution_context",
    ]

    for attr_name in dir(OpExecutionContext):
        if attr_name.startswith("__") or attr_name in ignores:
            continue
        if hasattr(AssetExecutionContext, attr_name):
            op_attr = getattr(OpExecutionContext, attr_name)
            asset_attr = getattr(AssetExecutionContext, attr_name)

            assert op_attr.__doc__ == asset_attr.__doc__


def test_deprecation_warnings():
    # Test that every method on OpExecutionContext is either reimplemented by AssetExecutionContext
    # or throws a deprecation warning on AssetExecutionContext. This will allow us to eventually make
    # AssetExecutionContext not a subclass of OpExecutionContext without doing a breaking change.

    # If this test fails, it is likely because you added a method to OpExecutionContext without
    # also adding that method to AssetExecutionContext. Please add the same method to AssetExecutionContext
    # with an appropriate deprecation warning (see existing deprecated methods for examples).
    # If the method should not be deprecated for AssetExecutionContext, please still add the same method
    # to AssetExecutionContext and add the method name to asset_context_not_deprecated

    # This list maintains all methods on OpExecutionContext that are not deprecated on AssetExecutionContext
    asset_context_not_deprecated = [
        "add_output_metadata",
        "asset_check_spec",
        "asset_checks_def",
        "asset_key",
        "asset_key_for_input",
        "asset_key_for_output",
        "asset_partition_key_for_input",
        "asset_partition_key_for_output",
        "asset_partition_key_range",
        "asset_partition_key_range_for_input",
        "asset_partition_key_range_for_output",
        "asset_partition_keys_for_input",
        "asset_partition_keys_for_output",
        "asset_partitions_def_for_input",
        "asset_partitions_def_for_output",
        "asset_partitions_time_window_for_input",
        "asset_partitions_time_window_for_output",
        "assets_def",
        "dagster_run",
        "get_output_metadata",
        "get_tag",
        "has_asset_checks_def",
        "has_partition_key",
        "has_tag",
        "instance",
        "job_name",
        "log",
        "op_handle",
        "output_for_asset_key",
        "partition_key",
        "partition_key_range",
        "partition_time_window",
        "pdb",
        "requires_typed_event_stream",
        "resources",
        "run_tags",
        "selected_asset_check_keys",
        "selected_asset_keys",
        "selected_output_names",
        "set_data_version",
        "set_requires_typed_event_stream",
        "typed_event_stream_error_message",
        "describe_op",
        "file_manager",
        "has_assets_def",
        "get_mapping_key",
        "get_step_execution_context",
        "job_def",
        "node_handle",
        "op",
        "op_config",
        "op_def",
        "op_handle",
        "step_launcher",
        "has_events",
        "consume_events",
        "log_event",
        "get_asset_provenance",
        "is_subset",
        "partition_keys",
        "get",
    ]

    other_ignores = [
        "_abc_impl",
        "_events",
        "_output_metadata",
        "_pdb",
        "_step_execution_context",
    ]

    def assert_deprecation_messages_as_expected(received_info, expected_info):
        assert received_info.breaking_version == expected_info["breaking_version"]
        assert received_info.additional_warn_text == expected_info["additional_warn_text"]
        assert received_info.subject == expected_info["subject"]

    for attr in dir(OpExecutionContext):
        if attr.startswith("__") or attr in other_ignores:
            continue
        if not hasattr(AssetExecutionContext, attr):
            raise Exception(
                f"Property {attr} on OpExecutionContext does not have an implementation on"
                " AssetExecutionContext. All properties on OpExecutionContext must be"
                " re-implemented on AssetExecutionContext with appropriate deprecation"
                " warnings. See the class implementation of AssetExecutionContext for more details."
            )

        asset_context_attr = getattr(AssetExecutionContext, attr)

        if attr not in asset_context_not_deprecated:
            if not hasattr(asset_context_attr.fget, "_deprecated"):
                raise Exception(
                    f"Property {attr} on OpExecutionContext is implemented but not deprecated on"
                    " AssetExecutionContext. If this in intended, update asset_context_not_deprecated."
                    f" Otherwise, add a deprecation warning to {attr}."
                )

            deprecation_info = asset_context_attr.fget._deprecated  # noqa: SLF001
            expected_deprecation_args = _get_deprecation_kwargs(attr)
            assert_deprecation_messages_as_expected(deprecation_info, expected_deprecation_args)


def test_instance_check():
    # turn off any outer warnings filters, e.g. ignores that are set in pyproject.toml
    warnings.resetwarnings()
    warnings.filterwarnings("error")

    @asset
    def test_op_context_instance_check(context: AssetExecutionContext):
        isinstance(context, OpExecutionContext)

    with pytest.raises(DeprecationWarning):
        materialize([test_op_context_instance_check])

    @asset
    def test_asset_context_instance_check(context: AssetExecutionContext):
        isinstance(context, AssetExecutionContext)

    assert materialize([test_asset_context_instance_check]).success
