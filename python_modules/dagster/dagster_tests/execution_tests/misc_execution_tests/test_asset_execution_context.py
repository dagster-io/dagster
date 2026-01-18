import dagster as dg


def test_doc_strings():
    """Tests that methods on AssetExecutionContext correctly get their doc strings from the corresponding
    method on OpExecutionContext.
    """
    ignores = [
        "_abc_impl",
        "_events",
        "_output_metadata",
        "_pdb",
        "_step_execution_context",
        # methods that have re-written docs strings
        "pdb",
        "run",
        "job_def",
        "log",
    ]

    for attr_name in dir(dg.OpExecutionContext):
        if attr_name.startswith("__") or attr_name in ignores:
            continue
        if hasattr(dg.AssetExecutionContext, attr_name):
            op_attr = getattr(dg.OpExecutionContext, attr_name)
            asset_attr = getattr(dg.AssetExecutionContext, attr_name)

            assert op_attr.__doc__ == asset_attr.__doc__
