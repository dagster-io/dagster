import groupBy from 'lodash/groupBy';
import keyBy from 'lodash/keyBy';
import reject from 'lodash/reject';
import {useMemo} from 'react';

import {ASSET_NODE_FRAGMENT} from './AssetNode';
import {GraphData, buildGraphData, toGraphId, tokenForAssetKey} from './Utils';
import {
  AssetGraphQuery,
  AssetGraphQueryVariables,
  AssetGraphQueryVersion,
  AssetNodeForGraphQueryFragment,
} from './types/useAssetGraphData.types';
import {gql} from '../apollo-client';
import {usePrefixedCacheKey} from '../app/AppProvider';
import {GraphQueryItem, filterByQuery} from '../app/GraphQueryImpl';
import {AssetKey} from '../assets/types';
import {AssetGroupSelector, PipelineSelector} from '../graphql/types';
import {useIndexedDBCachedQuery} from '../search/useIndexedDBCachedQuery';
import {doesFilterArrayMatchValueArray} from '../ui/Filters/useAssetTagFilter';

export interface AssetGraphFetchScope {
  hideEdgesToNodesOutsideQuery?: boolean;
  hideNodesMatching?: (node: AssetNodeForGraphQueryFragment) => boolean;
  pipelineSelector?: PipelineSelector;
  groupSelector?: AssetGroupSelector;
  kinds?: string[];
}

export type AssetGraphQueryItem = GraphQueryItem & {
  node: AssetNode;
};

export function useFullAssetGraphData(options: AssetGraphFetchScope) {
  const fetchResult = useIndexedDBCachedQuery<AssetGraphQuery, AssetGraphQueryVariables>({
    query: ASSET_GRAPH_QUERY,
    variables: useMemo(
      () => ({
        pipelineSelector: options.pipelineSelector,
        groupSelector: options.groupSelector,
      }),
      [options.pipelineSelector, options.groupSelector],
    ),
    key: usePrefixedCacheKey(
      `AssetGraphQuery/${JSON.stringify({
        pipelineSelector: options.pipelineSelector,
        groupSelector: options.groupSelector,
      })}`,
    ),
    version: AssetGraphQueryVersion,
  });

  const nodes = fetchResult.data?.assetNodes;
  const queryItems = useMemo(() => (nodes ? buildGraphQueryItems(nodes) : []), [nodes]);

  const fullAssetGraphData = useMemo(
    () => (queryItems ? buildGraphData(queryItems.map((n) => n.node)) : null),
    [queryItems],
  );
  return fullAssetGraphData;
}

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
  const fetchResult = useIndexedDBCachedQuery<AssetGraphQuery, AssetGraphQueryVariables>({
    query: ASSET_GRAPH_QUERY,
    variables: useMemo(
      () => ({
        pipelineSelector: options.pipelineSelector,
        groupSelector: options.groupSelector,
      }),
      [options.pipelineSelector, options.groupSelector],
    ),
    key: usePrefixedCacheKey(
      `AssetGraphQuery/${JSON.stringify({
        pipelineSelector: options.pipelineSelector,
        groupSelector: options.groupSelector,
      })}`,
    ),
    version: AssetGraphQueryVersion,
  });

  const nodes = fetchResult.data?.assetNodes;

  const repoFilteredNodes = useMemo(() => {
    // Apply any filters provided by the caller. This is where we do repo filtering
    let matching = nodes;
    if (options.hideNodesMatching) {
      matching = reject(matching, options.hideNodesMatching);
    }
    return matching;
  }, [nodes, options.hideNodesMatching]);

  const graphQueryItems = useMemo(
    () => (repoFilteredNodes ? buildGraphQueryItems(repoFilteredNodes) : []),
    [repoFilteredNodes],
  );

  const {assetGraphData, graphAssetKeys, allAssetKeys} = useMemo(() => {
    if (repoFilteredNodes === undefined || graphQueryItems === undefined) {
      return {
        graphAssetKeys: [],
        graphQueryItems: [],
        assetGraphData: null,
      };
    }

    // Filter the set of all AssetNodes down to those matching the `opsQuery`.
    // In the future it might be ideal to move this server-side, but we currently
    // get to leverage the useQuery cache almost 100% of the time above, making this
    // super fast after the first load vs a network fetch on every page view.
    const {all: allFilteredByOpQuery} = filterByQuery(graphQueryItems, opsQuery);
    const kinds = options.kinds?.map((c) => c.toLowerCase());
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
    if (options.hideEdgesToNodesOutsideQuery) {
      removeEdgesToHiddenAssets(assetGraphData, repoFilteredNodes);
    }

    return {
      allAssetKeys: repoFilteredNodes.map((n) => n.assetKey),
      graphAssetKeys: all.map((n) => ({path: n.node.assetKey.path})),
      assetGraphData,
      graphQueryItems,
    };
  }, [
    repoFilteredNodes,
    graphQueryItems,
    opsQuery,
    options.kinds,
    options.hideEdgesToNodesOutsideQuery,
  ]);

  return {
    fetchResult,
    assetGraphData,
    graphQueryItems,
    graphAssetKeys,
    allAssetKeys,
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

  let upstreamDepth = -1;
  let candidates = new Set([start.name]);

  while (candidates.size > 0) {
    const nextCandidates: Set<string> = new Set();
    upstreamDepth += 1;

    candidates.forEach((candidate) => {
      map[candidate]!.inputs.flatMap((i) =>
        i.dependsOn.forEach((d) => {
          if (!candidates.has(d.solid.name)) {
            nextCandidates.add(d.solid.name);
          }
        }),
      );
    });
    candidates = nextCandidates;
  }

  let downstreamDepth = -1;
  candidates = new Set([start.name]);

  while (candidates.size > 0) {
    const nextCandidates: Set<string> = new Set();
    downstreamDepth += 1;

    candidates.forEach((candidate) => {
      map[candidate]!.outputs.flatMap((i) =>
        i.dependedBy.forEach((d) => {
          if (!candidates.has(d.solid.name)) {
            nextCandidates.add(d.solid.name);
          }
        }),
      );
    });
    candidates = nextCandidates;
  }

  return {
    upstream: upstreamDepth,
    downstream: downstreamDepth,
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
    changedReasons
    tags {
      key
      value
    }
    owners {
      ... on TeamAssetOwner {
        team
      }
      ... on UserAssetOwner {
        email
      }
    }
    tags {
      key
      value
    }
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
