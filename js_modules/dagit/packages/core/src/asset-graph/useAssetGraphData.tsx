import {gql, useQuery} from '@apollo/client';
import groupBy from 'lodash/groupBy';
import keyBy from 'lodash/keyBy';
import reject from 'lodash/reject';
import React from 'react';

import {filterByQuery, GraphQueryItem} from '../app/GraphQueryImpl';
import {AssetKey} from '../assets/types';
import {AssetGroupSelector, PipelineSelector} from '../types/globalTypes';

import {ASSET_NODE_FRAGMENT} from './AssetNode';
import {buildGraphData, GraphData, toGraphId, tokenForAssetKey} from './Utils';
import {
  AssetGraphQuery,
  AssetGraphQueryVariables,
  AssetGraphQuery_assetNodes,
} from './types/AssetGraphQuery';

export interface AssetGraphFetchScope {
  hideEdgesToNodesOutsideQuery?: boolean;
  hideNodesMatching?: (node: AssetGraphQuery_assetNodes) => boolean;
  pipelineSelector?: PipelineSelector;
  groupSelector?: AssetGroupSelector;
}

export type AssetGraphQueryItem = GraphQueryItem & {
  node: AssetNode;
};

/** Fetches data for rendering an asset graph:
 *
 * @param pipelineSelector: Optionally scope to an asset job, or pass null for the global graph
 *
 * @param opsQuery: filter the returned graph using selector syntax string (eg: asset_name++)
 *
 * @param filterNodes: filter the returned graph using the provided function. The global graph
 * uses this option to implement the "3 of 4 repositories" picker.
 */
export function useAssetGraphData(opsQuery: string, options: AssetGraphFetchScope) {
  const fetchResult = useQuery<AssetGraphQuery, AssetGraphQueryVariables>(ASSET_GRAPH_QUERY, {
    notifyOnNetworkStatusChange: true,
    variables: {
      pipelineSelector: options.pipelineSelector,
      groupSelector: options.groupSelector,
    },
  });

  const nodes = fetchResult.data?.assetNodes;

  const {
    assetGraphData,
    graphQueryItems,
    graphAssetKeys,
    allAssetKeys,
    applyingEmptyDefault,
  } = React.useMemo(() => {
    if (nodes === undefined) {
      return {
        graphAssetKeys: [],
        graphQueryItems: [],
        assetGraphData: null,
        applyingEmptyDefault: false,
      };
    }

    // Apply any filters provided by the caller. This is where we do repo filtering
    let matching = nodes;
    if (options.hideNodesMatching) {
      matching = reject(matching, options.hideNodesMatching);
    }

    // Filter the set of all AssetNodes down to those matching the `opsQuery`.
    // In the future it might be ideal to move this server-side, but we currently
    // get to leverage the useQuery cache almost 100% of the time above, making this
    // super fast after the first load vs a network fetch on every page view.
    const graphQueryItems = buildGraphQueryItems(matching);
    const {all, applyingEmptyDefault} = filterByQuery(graphQueryItems, opsQuery);

    // Assemble the response into the data structure used for layout, traversal, etc.
    const assetGraphData = buildGraphData(all.map((n) => n.node));
    if (options.hideEdgesToNodesOutsideQuery) {
      removeEdgesToHiddenAssets(assetGraphData, nodes);
    }

    return {
      allAssetKeys: matching.map((n) => n.assetKey),
      graphAssetKeys: all.map((n) => ({path: n.node.assetKey.path})),
      assetGraphData,
      graphQueryItems,
      applyingEmptyDefault,
    };
  }, [nodes, opsQuery, options.hideEdgesToNodesOutsideQuery, options.hideNodesMatching]);

  return {
    fetchResult,
    assetGraphData,
    graphQueryItems,
    graphAssetKeys,
    allAssetKeys,
    applyingEmptyDefault,
  };
}

type AssetNode = AssetGraphQuery_assetNodes;

const buildGraphQueryItems = (nodes: AssetNode[]) => {
  const items: {[name: string]: AssetGraphQueryItem} = {};

  for (const node of nodes) {
    const name = tokenForAssetKey(node.assetKey);
    items[name] = {
      node,
      name,
      inputs: node.dependencyKeys.map((key) => ({
        dependsOn: [{solid: {name: tokenForAssetKey(key)}}],
      })),
      outputs: node.dependedByKeys.map((key) => ({
        dependedBy: [{solid: {name: tokenForAssetKey(key)}}],
      })),
    };
  }
  return Object.values(items);
};

const removeEdgesToHiddenAssets = (graphData: GraphData, allNodes: AssetNode[]) => {
  const allNodesById = groupBy(allNodes, (n) => toGraphId(n.assetKey));
  const notSourceAsset = (id: string) => !!allNodesById[id];

  for (const node of Object.keys(graphData.upstream)) {
    for (const edge of Object.keys(graphData.upstream[node])) {
      if (!graphData.nodes[edge] && notSourceAsset(node)) {
        delete graphData.upstream[node][edge];
        delete graphData.downstream[edge][node];
      }
    }
  }

  for (const node of Object.keys(graphData.downstream)) {
    for (const edge of Object.keys(graphData.downstream[node])) {
      if (!graphData.nodes[edge] && notSourceAsset(node)) {
        delete graphData.upstream[edge][node];
        delete graphData.downstream[node][edge];
      }
    }
  }
};

export const calculateGraphDistances = (items: GraphQueryItem[], assetKey: AssetKey) => {
  const map = keyBy(items, (g) => g.name);
  const start = map[tokenForAssetKey(assetKey)];
  if (!start) {
    return {upstream: 0, downstream: 0};
  }

  const bfsUpstream = (ins: GraphQueryItem['inputs'], depth: number): number => {
    const next = ins
      .flatMap((i) => i.dependsOn.map((d) => d.solid.name))
      .map((name) => map[name].inputs);

    return Math.max(depth, ...next.map((nextIns) => bfsUpstream(nextIns, depth + 1)));
  };
  const bfsDownstream = (outs: GraphQueryItem['outputs'], depth: number): number => {
    const next = outs
      .flatMap((i) => i.dependedBy.map((d) => d.solid.name))
      .map((name) => map[name].outputs);

    return Math.max(depth, ...next.map((nextOuts) => bfsDownstream(nextOuts, depth + 1)));
  };

  return {
    upstream: bfsUpstream(start.inputs, 0),
    downstream: bfsDownstream(start.outputs, 0),
  };
};

const ASSET_GRAPH_QUERY = gql`
  query AssetGraphQuery($pipelineSelector: PipelineSelector, $groupSelector: AssetGroupSelector) {
    assetNodes(pipeline: $pipelineSelector, group: $groupSelector) {
      id
      groupName
      repository {
        id
        name
        location {
          id
          name
        }
      }
      dependencyKeys {
        path
      }
      dependedByKeys {
        path
      }
      ...AssetNodeFragment
    }
  }
  ${ASSET_NODE_FRAGMENT}
`;
