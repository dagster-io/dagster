import inspect
import warnings

import pytest
from dagster import AssetExecutionContext, OpExecutionContext, asset, materialize
from dagster._core.execution.context.compute import _get_deprecation_kwargs


def test_deprecation_warnings():
    # Test that every method on OpExecutionContext is either reimplemented by AssetExecutionContext
    # or throws a deprecation warning on AssetExecutionContext

    # If this test fails, it is likely because you added a method to OpExecutionContext without
    # also adding that method to AssetExecutionContext. Please add the same method to AssetExecutionContext
    # with an appropriate deprecation warning (see existing deprecated methods for examples).
    # If the method should not be deprecated for AssetExecutionContext, please still add the same method
    # to AssetExecutionContext and add the method name to asset_execution_context_attrs

    asset_execution_context_attrs = [
        "op_execution_context",
        "is_asset_step",
        "asset_key",
        "asset_keys",
        "provenance",
        "provenance_by_asset_key",
        "code_version",
        "code_version_by_asset_key",
        "is_partition_step",
        "partition_key",
        "partition_key_range",
        "partition_time_window",
        "run_id",
        "job_name",
        "retry_number",
        "dagster_run",
        "pdb",
        "log",
        "log_event",
        "assets_def",
        "selected_asset_keys",
        "get_asset_provenance",
        "get_assets_code_version",
        "asset_check_spec",
        "partition_key_range_for_asset_key",
        "instance",
        # TODO - potentially remove below if they get deprecated
        "resources",
        "run_config",
    ]

    other_ignores = [
        "_abc_impl",
        # TODO - what to do about instance vars for OpExecutionContext? listed below
        "_events",
        "_output_metadata",
        "_pdb",
        "_step_execution_context",
    ]

    def assert_deprecation_messages_as_expected(recieved_info, expected_info):
        assert recieved_info.breaking_version == expected_info["breaking_version"]
        assert recieved_info.additional_warn_text == expected_info["additional_warn_text"]
        assert recieved_info.subject == expected_info["subject"]

    @asset
    def test_context(context: AssetExecutionContext):
        asset_context = context
        op_context = context.op_execution_context

        op_context_properties = []

        for attr in dir(OpExecutionContext):
            if isinstance(getattr(OpExecutionContext, attr), property):
                op_context_properties.append(attr)
                if attr in asset_execution_context_attrs:
                    continue
                try:
                    deprecation_info = getattr(  # noqa: SLF001
                        AssetExecutionContext, attr
                    ).fget._deprecated

                except Exception:
                    raise Exception(
                        f"Property {attr} on OpExecutionContext does not have an implementation on"
                        " AssetExecutionContext. All methods on OpExecutionContext must be"
                        " re-implemented on AssetExecutionContext with appropriate deprecation"
                        " warnings. See the class implementation of AssetExecutionContext for more"
                        " details."
                    )

                expected_deprecation_args = _get_deprecation_kwargs(attr)
                assert_deprecation_messages_as_expected(deprecation_info, expected_deprecation_args)

        for method in dir(op_context):
            if (
                method in asset_execution_context_attrs
                or method[:2] == "__"
                or method in op_context_properties
                or method in other_ignores
            ):
                continue
            if inspect.ismethod(getattr(op_context, method)):
                assert method in dir(asset_context)
                try:
                    deprecation_info = getattr(asset_context, method)._deprecated  # noqa: SLF001
                except Exception:
                    raise Exception(
                        f"Method {method} on OpExecutionContext does not have an implementation on"
                        " AssetExecutionContext. All methods on OpExecutionContext must be"
                        " re-implemented on AssetExecutionContext with appropriate deprecation"
                        " warnings. See the class implementation of AssetExecutionContext for more"
                        " details."
                    )

                expected_deprecation_args = _get_deprecation_kwargs(method)
                assert_deprecation_messages_as_expected(deprecation_info, expected_deprecation_args)
            else:
                raise Exception(
                    f"Attribute {method} not accounted for in AssetExecutionContext deprecation"
                    " test"
                )

    materialize([test_context])


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

    materialize([test_asset_context_instance_check])
