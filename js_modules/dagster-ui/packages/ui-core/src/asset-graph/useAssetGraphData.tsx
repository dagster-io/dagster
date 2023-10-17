import {gql, useQuery} from '@apollo/client';
import groupBy from 'lodash/groupBy';
import keyBy from 'lodash/keyBy';
import reject from 'lodash/reject';
import React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {filterByQuery, GraphQueryItem} from '../app/GraphQueryImpl';
import {AssetKey} from '../assets/types';
import {asyncGetFullAssetLayoutIndexDB} from '../graph/asyncGraphLayout';
import {AssetGroupSelector, PipelineSelector} from '../graphql/types';

import {ASSET_NODE_FRAGMENT} from './AssetNode';
import {buildGraphData, GraphData, toGraphId, tokenForAssetKey} from './Utils';
import {
  AssetGraphQuery,
  AssetGraphQueryVariables,
  AssetNodeForGraphQueryFragment,
} from './types/useAssetGraphData.types';

export interface AssetGraphFetchScope {
  hideEdgesToNodesOutsideQuery?: boolean;
  hideNodesMatching?: (node: AssetNodeForGraphQueryFragment) => boolean;
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

  const repoFilteredNodes = React.useMemo(() => {
    // Apply any filters provided by the caller. This is where we do repo filtering
    let matching = nodes;
    if (options.hideNodesMatching) {
      matching = reject(matching, options.hideNodesMatching);
    }
    return matching;
  }, [nodes, options.hideNodesMatching]);

  const graphQueryItems = React.useMemo(
    () => (repoFilteredNodes ? buildGraphQueryItems(repoFilteredNodes) : []),
    [repoFilteredNodes],
  );

  const fullGraphQueryItems = React.useMemo(
    () => (nodes ? buildGraphQueryItems(nodes) : []),
    [nodes],
  );

  const fullAssetGraphData = React.useMemo(
    () => (fullGraphQueryItems ? buildGraphData(fullGraphQueryItems.map((n) => n.node)) : null),
    [fullGraphQueryItems],
  );

  const {assetGraphData, graphAssetKeys, allAssetKeys, applyingEmptyDefault} = React.useMemo(() => {
    if (repoFilteredNodes === undefined || graphQueryItems === undefined) {
      return {
        graphAssetKeys: [],
        graphQueryItems: [],
        assetGraphData: null,
        applyingEmptyDefault: false,
      };
    }

    // Filter the set of all AssetNodes down to those matching the `opsQuery`.
    // In the future it might be ideal to move this server-side, but we currently
    // get to leverage the useQuery cache almost 100% of the time above, making this
    // super fast after the first load vs a network fetch on every page view.
    const {all, applyingEmptyDefault} = filterByQuery(graphQueryItems, opsQuery);

    // Assemble the response into the data structure used for layout, traversal, etc.
    const assetGraphData = buildGraphData(all.map((n) => n.node));
    if (options.hideEdgesToNodesOutsideQuery) {
      removeEdgesToHiddenAssets(assetGraphData, repoFilteredNodes);
    }

    return {
      allAssetKeys: repoFilteredNodes.map((n) => n.assetKey),
      graphAssetKeys: all.map((n) => ({path: n.node.assetKey.path})),
      assetGraphData,
      graphQueryItems,
      applyingEmptyDefault,
    };
  }, [repoFilteredNodes, graphQueryItems, opsQuery, options.hideEdgesToNodesOutsideQuery]);

  // Used to avoid showing "query error"
  const [isCalculating, setIsCalculating] = React.useState<boolean>(true);
  const [isCached, setIsCached] = React.useState<boolean>(false);
  const [assetGraphDataMaybeCached, setAssetGraphDataMaybeCached] =
    React.useState<GraphData | null>(null);

  const {flagDisableDAGCache} = useFeatureFlags();

  React.useLayoutEffect(() => {
    setAssetGraphDataMaybeCached(null);
    setIsCached(false);
    setIsCalculating(true);
    (async () => {
      let fullAssetGraphData = null;
      if (applyingEmptyDefault && repoFilteredNodes && !flagDisableDAGCache) {
        // build the graph data anyways to check if it's cached
        const {all} = filterByQuery(graphQueryItems, '*');
        fullAssetGraphData = buildGraphData(all.map((n) => n.node));
        if (options.hideEdgesToNodesOutsideQuery) {
          removeEdgesToHiddenAssets(fullAssetGraphData, repoFilteredNodes);
        }
        if (fullAssetGraphData) {
          const isCached = await asyncGetFullAssetLayoutIndexDB.isCached(fullAssetGraphData);
          if (isCached) {
            setAssetGraphDataMaybeCached(fullAssetGraphData);
            setIsCached(true);
            setIsCalculating(false);
            return;
          }
        }
      }
      setAssetGraphDataMaybeCached(assetGraphData);
      setIsCached(false);
      setIsCalculating(false);
    })();
  }, [
    applyingEmptyDefault,
    graphQueryItems,
    options.hideEdgesToNodesOutsideQuery,
    repoFilteredNodes,
    assetGraphData,
    flagDisableDAGCache,
  ]);

  return {
    fetchResult,
    assetGraphData: assetGraphDataMaybeCached,
    fullAssetGraphData,
    graphQueryItems,
    graphAssetKeys,
    allAssetKeys,
    applyingEmptyDefault: applyingEmptyDefault && !isCached,
    isCalculating,
  };
}

type AssetNode = AssetNodeForGraphQueryFragment;

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
    for (const edge of Object.keys(graphData.upstream[node]!)) {
      if (!graphData.nodes[edge] && notSourceAsset(node)) {
        delete graphData.upstream[node]![edge];
        delete graphData.downstream[edge]![node];
      }
    }
  }

  for (const node of Object.keys(graphData.downstream)) {
    for (const edge of Object.keys(graphData.downstream[node]!)) {
      if (!graphData.nodes[edge] && notSourceAsset(node)) {
        delete graphData.upstream[edge]![node];
        delete graphData.downstream[node]![edge];
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

  const dfsUpstream = (name: string, depth: number): number => {
    const next = map[name]!.inputs.flatMap((i) => i.dependsOn.map((d) => d.solid.name)).filter(
      (dname) => dname !== name,
    );

    return Math.max(depth, ...next.map((dname) => dfsUpstream(dname, depth + 1)));
  };
  const dfsDownstream = (name: string, depth: number): number => {
    const next = map[name]!.outputs.flatMap((i) => i.dependedBy.map((d) => d.solid.name)).filter(
      (dname) => dname !== name,
    );

    return Math.max(depth, ...next.map((dname) => dfsDownstream(dname, depth + 1)));
  };

  return {
    upstream: dfsUpstream(start.name, 0),
    downstream: dfsDownstream(start.name, 0),
  };
};

export const ASSET_GRAPH_QUERY = gql`
  query AssetGraphQuery($pipelineSelector: PipelineSelector, $groupSelector: AssetGroupSelector) {
    assetNodes(pipeline: $pipelineSelector, group: $groupSelector) {
      id
      ...AssetNodeForGraphQuery
    }
  }

  fragment AssetNodeForGraphQuery on AssetNode {
    id
    groupName
    isExecutable
    hasMaterializePermission
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

  ${ASSET_NODE_FRAGMENT}
`;
