from dagster._core.definitions.decorators import asset, asset_group

def test_asset_group_context_manager():
    assets = {}
    with asset_group("group1"):
        @asset
        def asset1():
            return 1
        @asset
        def asset2():
            return 2
        assets["asset1"] = asset1
        assets["asset2"] = asset2
    with asset_group("group2"):
        @asset
        def asset3():
            return 3
        @asset
        def asset4():
            return 4
        assets["asset3"] = asset3
        assets["asset4"] = asset4
    assert assets["asset1"].group_names_by_key[assets["asset1"].key] == "group1"
    assert assets["asset2"].group_names_by_key[assets["asset2"].key] == "group1"
    assert assets["asset3"].group_names_by_key[assets["asset3"].key] == "group2"
    assert assets["asset4"].group_names_by_key[assets["asset4"].key] == "group2"
