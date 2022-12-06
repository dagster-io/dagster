# start_single_asset
@asset(code_version="1")
def asset_with_version():
    return 100
# end_single_asset

# start_multi_asset
@multi_asset(
  outs={
      "a": AssetOut(code_version="1"),
      "b": AssetOut(code_version="2"),
    }
)
def asset_with_version():
    yield Output(100, "a")
    yield Output(200, "b")
# end_multi_asset
