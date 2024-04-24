from dagster import AutoMaterializePolicy, asset, default_asset_attrs


def test_default_asset_attrs():
    with default_asset_attrs(
        group_name="marketing", auto_materialize_policy=AutoMaterializePolicy.eager()
    ):

        @asset
        def asset1(): ...

        @asset(group_name="override")
        def asset2(): ...

    @asset
    def asset3(): ...

    assert next(iter(asset1.group_names_by_key.values())) == "marketing"
    assert next(iter(asset2.group_names_by_key.values())) == "override"
    assert next(iter(asset3.group_names_by_key.values())) == "default"
    assert (
        next(iter(asset1.auto_materialize_policies_by_key.values()))
        == AutoMaterializePolicy.eager()
    )
    assert (
        next(iter(asset2.auto_materialize_policies_by_key.values()))
        == AutoMaterializePolicy.eager()
    )
    assert len(asset3.auto_materialize_policies_by_key) == 0


def test_default_asset_attrs_nested():
    with default_asset_attrs(group_name="marketing"):
        with default_asset_attrs(auto_materialize_policy=AutoMaterializePolicy.eager()):

            @asset
            def asset1(): ...

            @asset(group_name="marketing_override")
            def asset1_and_half(): ...

        @asset
        def asset2(): ...

    @asset
    def asset3(): ...

    assert next(iter(asset1.group_names_by_key.values())) == "marketing"
    assert next(iter(asset1_and_half.group_names_by_key.values())) == "marketing_override"
    assert next(iter(asset2.group_names_by_key.values())) == "marketing"
    assert next(iter(asset3.group_names_by_key.values())) == "default"
    assert (
        next(iter(asset1.auto_materialize_policies_by_key.values()))
        == AutoMaterializePolicy.eager()
    )
    assert len(asset2.auto_materialize_policies_by_key) == 0
    assert len(asset3.auto_materialize_policies_by_key) == 0
