from shared.factory import asset_factory  # ty: ignore[unresolved-import]

asset_configurations = [
    "asset_1",
    "asset_2",
    "asset_3",
]


my_codespace_assets = [asset_factory(asset) for asset in asset_configurations]
