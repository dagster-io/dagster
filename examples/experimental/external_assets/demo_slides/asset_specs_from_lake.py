def asset_specs_from_de_dsl(path) -> List[AssetSpec]:
    return [
        AssetSpec(
            key=AssetKey(asset["name"].split("/")),
            deps=get_deps(asset),
            group_name="external_assets",
        )
        for asset in load_yaml(path)["assets"]
    ]


defs = Definitions(assets=external_assets_from_specs(asset_specs_from_de_dsl("lake.yaml")))
