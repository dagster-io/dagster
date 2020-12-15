from typing import Dict, List, Optional, Set

from dagster.core.selector.subset_selector import clause_to_subset, parse_clause
from lakehouse.asset import Asset
from lakehouse.errors import LakehouseAssetQueryError


class QueryableAssetSet:
    def __init__(self, assets: List[Asset]):
        self._assets_by_path_str = {path_str(asset): asset for asset in assets}
        self._dep_graph = generate_dep_graph(assets)

    def query_assets(self, query: Optional[str]) -> List[Asset]:
        """Returns all assets that match the query.  The supported query syntax is described in
        detail at https://docs.dagster.io/overview/solid-selection.
        """
        if query is None:
            return list(self._assets_by_path_str.values())

        queried_asset_path = parse_clause(query)[1]
        if queried_asset_path not in self._assets_by_path_str.keys():
            raise LakehouseAssetQueryError(f"{queried_asset_path} does not exist in set of assets.")

        return [self._assets_by_path_str[pstr] for pstr in clause_to_subset(self._dep_graph, query)]


def generate_dep_graph(assets) -> Dict[str, Dict[str, Set[str]]]:
    # defaultdict isn't appropriate because we also want to include items without dependencies
    graph = {"upstream": {}, "downstream": {}}
    for asset in assets:
        graph["upstream"][path_str(asset)] = set()
        graph["downstream"].setdefault(path_str(asset), set())
        if asset.computation:
            for dep in asset.computation.deps.values():
                graph["upstream"][path_str(asset)].add(path_str(dep.asset))
                graph["downstream"].setdefault(path_str(dep.asset), set()).add(path_str(asset))

    return graph


def path_str(asset: Asset) -> str:
    return ".".join(asset.path)
