# start_file
import pandas as pd

import dagster as dg


@dg.multi_asset(
    specs=[
        dg.AssetSpec(
            ["core", "fix", "index_metadata"], deps=["instruments", "weights"]
        ),
        dg.AssetSpec(["core", "fix", "index_weights"], deps=["instruments", "weights"]),
    ]
)
def index_multi_asset(
    instruments: pd.DataFrame,
    weights: pd.DataFrame,
):
    yield dg.MaterializeResult(
        asset_key=["core", "fix", "index_metadata"],
        metadata={"num_rows": len(instruments)},
    )
    yield dg.MaterializeResult(
        asset_key=["core", "fix", "index_weights"], metadata={"num_rows": len(weights)}
    )


# end_file


# start_test
class MockDataIOManager(dg.IOManager):
    def __init__(self, instruments_df, weights_df):
        self.instruments_df = instruments_df
        self.weights_df = weights_df

    def load_input(self, context):
        asset_key_path = context.asset_key.path
        if asset_key_path == ["instruments"]:
            return self.instruments_df
        elif asset_key_path == ["weights"]:
            return self.weights_df
        else:
            raise ValueError(f"Unexpected asset key: {asset_key_path}")

    def handle_output(self, context, obj):
        pass


def test_with_define_asset_job_approach():
    test_instruments = pd.DataFrame({})
    test_weights = pd.DataFrame({})

    # Define source assets - keys must match the parameter names
    source_instruments = dg.SourceAsset(key="instruments")
    source_weights = dg.SourceAsset(key="weights")

    defs = dg.Definitions(
        assets=[
            source_instruments,
            source_weights,
            index_multi_asset,
        ],
        resources={
            "io_manager": MockDataIOManager(
                instruments_df=test_instruments,
                weights_df=test_weights,
            )
        },
    )

    job = defs.get_implicit_global_asset_job_def()
    result = job.execute_in_process(
        asset_selection=[
            dg.AssetKey(["core", "fix", "index_metadata"]),
            dg.AssetKey(["core", "fix", "index_weights"]),
        ]
    )

    assert result.success


# end_test
