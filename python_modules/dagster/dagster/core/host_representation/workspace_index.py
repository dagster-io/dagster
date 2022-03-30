from dagster import check
from dagster.core.workspace.workspace import WorkspaceLocationEntry
from dagster.core.host_representation.external_data import (
    ExternalAssetNode,
    ExternalAssetDependency,
)


class WorkspaceIndex:
    def __init__(self, workspace_snapshot):
        self.workspace_snapshot = check.dict_param(
            workspace_snapshot,
            "workspace_snapshot",
            key_type=str,
            value_type=WorkspaceLocationEntry,
        )
        self._external_asset_deps = {}
        self._sink_assets = {}
        # self.build_external_asset_deps()

    def build_external_asset_deps(self):
        depended_by_assets_by_source_asset = (
            {}
        )  # key is asset key, value is list of DependedBy ExternalAssetNodes
        map_defined_asset_to_location = (
            {}
        )  # key is asset key, value is tuple (location_name, repo_name)
        for location_entry in self.workspace_snapshot.values():
            repo_location = location_entry.repository_location
            if repo_location:
                repositories = repo_location.get_repositories()
                for repo_name, external_repo in repositories.items():
                    asset_nodes = external_repo.get_external_asset_nodes()
                    for asset_node in asset_nodes:
                        if not asset_node.op_name:  # is source asset
                            if asset_node.asset_key not in depended_by_assets_by_source_asset:
                                depended_by_assets_by_source_asset[asset_node.asset_key] = []
                            depended_by_assets_by_source_asset[asset_node.asset_key].extend(
                                asset_node.depended_by
                            )
                        else:
                            map_defined_asset_to_location[asset_node.asset_key] = (
                                repo_location.name,
                                repo_name,
                            )

        self._external_asset_deps = (
            {}
        )  # nested dict that maps dependedby assets by asset key by location tuple (repo_location.name, repo_name)
        for source_asset, depended_by_assets in depended_by_assets_by_source_asset.items():
            asset_def_location = map_defined_asset_to_location.get(source_asset, None)
            if asset_def_location:  # source asset is defined as asset in another repository
                if asset_def_location not in self._external_asset_deps:
                    self._external_asset_deps[asset_def_location] = {}
                if source_asset not in self._external_asset_deps[asset_def_location]:
                    self._external_asset_deps[asset_def_location][source_asset] = []
                self._external_asset_deps[asset_def_location][source_asset].extend(
                    depended_by_assets
                )
                for asset in depended_by_assets:
                    self._sink_assets[asset.key] = ExternalAssetNode(
                        asset_key=asset.key,
                        dependencies=[
                            ExternalAssetDependency(
                                upstream_asset_key=source_asset.key,
                                input_name=asset.input_name,
                                output_name=asset.output_name,
                            )
                        ],
                        depended_by=[],
                    )

        return self._external_asset_deps

    def get_external_asset_deps(self, repo_location_name, repo_name, asset_key):
        return self._external_asset_deps.get((repo_location_name, repo_name), {}).get(asset_key, [])
