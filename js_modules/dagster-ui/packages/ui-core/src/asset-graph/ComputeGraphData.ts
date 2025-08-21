import groupBy from 'lodash/groupBy';
import {filterAssetSelectionByQuery} from 'shared/asset-selection/filterAssetSelectionByQuery.oss';

import {ComputeGraphDataMessageType} from './ComputeGraphData.types';
import {GraphData, buildGraphData, toGraphId} from './Utils';
import {GraphDataState} from './useAssetGraphData';
import {doesFilterArrayMatchValueArray} from '../ui/Filters/doesFilterArrayMatchValueArray';
import {WorkspaceAssetFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';

export function computeGraphData({
  repoFilteredNodes,
  graphQueryItems,
  opsQuery,
  kinds: _kinds,
  hideEdgesToNodesOutsideQuery,
  supplementaryData,
}: Omit<ComputeGraphDataMessageType, 'id' | 'type'>): GraphDataState {
  if (repoFilteredNodes === undefined || graphQueryItems === undefined) {
    return {
      allAssetKeys: [],
      graphAssetKeys: [],
      assetGraphData: null,
    };
  }

  // Filter the set of all AssetNodes down to those matching the `opsQuery`.
  // In the future it might be ideal to move this server-side, but we currently
  // get to leverage the useQuery cache almost 100% of the time above, making this
  // super fast after the first load vs a network fetch on every page view.
  const {all: allFilteredByOpQuery} = filterAssetSelectionByQuery(
    graphQueryItems,
    opsQuery,
    supplementaryData,
  );
  const kinds = _kinds?.map((c) => c.toLowerCase());
  const all = kinds?.length
    ? allFilteredByOpQuery.filter(
        ({node}) =>
          node.kinds &&
          doesFilterArrayMatchValueArray(
            kinds,
            node.kinds.map((k) => k.toLowerCase()),
          ),
      )
    : allFilteredByOpQuery;

  // Assemble the response into the data structure used for layout, traversal, etc.
  const assetGraphData = buildGraphData(all.map((n) => n.node));
  if (hideEdgesToNodesOutsideQuery) {
    removeEdgesToHiddenAssets(assetGraphData, repoFilteredNodes);
  }

  return {
    allAssetKeys: repoFilteredNodes.map((n) => n.assetKey),
    graphAssetKeys: all.map((n) => ({path: n.node.assetKey.path})),
    assetGraphData,
  };
}

const removeEdgesToHiddenAssets = (graphData: GraphData, allNodes: WorkspaceAssetFragment[]) => {
  const allNodesById = groupBy(allNodes, (n) => toGraphId(n.assetKey));
  const notSourceAsset = (id: string) => !!allNodesById[id];

  for (const node of Object.keys(graphData.upstream)) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    for (const edge of Object.keys(graphData.upstream[node]!)) {
      if (!graphData.nodes[edge] && notSourceAsset(node)) {
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        delete graphData.upstream[node]![edge];
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        delete graphData.downstream[edge]![node];
      }
    }
  }

  for (const node of Object.keys(graphData.downstream)) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    for (const edge of Object.keys(graphData.downstream[node]!)) {
      if (!graphData.nodes[edge] && notSourceAsset(node)) {
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        delete graphData.upstream[edge]![node];
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        delete graphData.downstream[node]![edge];
      }
    }
  }
};
