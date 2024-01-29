from dagster import AssetExecutionContext, OpExecutionContext


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
