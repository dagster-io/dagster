import {memoize} from 'lodash';
import keyBy from 'lodash/keyBy';
import reject from 'lodash/reject';
import throttle from 'lodash/throttle';
import {useEffect, useMemo, useRef, useState} from 'react';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {ASSET_NODE_FRAGMENT} from './AssetNode';
import {GraphData, buildGraphData, tokenForAssetKey} from './Utils';
import {gql} from '../apollo-client';
import {computeGraphData as computeGraphDataImpl} from './ComputeGraphData';
import {ComputeGraphDataMessageType} from './ComputeGraphData.types';
import {featureEnabled} from '../app/Flags';
import {
  AssetGraphQuery,
  AssetGraphQueryVariables,
  AssetGraphQueryVersion,
  AssetNodeForGraphQueryFragment,
} from './types/useAssetGraphData.types';
import {usePrefixedCacheKey} from '../app/AppProvider';
import {GraphQueryItem} from '../app/GraphQueryImpl';
import {indexedDBAsyncMemoize} from '../app/Util';
import {AssetKey} from '../assets/types';
import {AssetGroupSelector, PipelineSelector} from '../graphql/types';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {useIndexedDBCachedQuery} from '../search/useIndexedDBCachedQuery';

export interface AssetGraphFetchScope {
  hideEdgesToNodesOutsideQuery?: boolean;
  hideNodesMatching?: (node: AssetNodeForGraphQueryFragment) => boolean;
  pipelineSelector?: PipelineSelector;
  groupSelector?: AssetGroupSelector;
  kinds?: string[];

  // This is used to indicate we shouldn't start handling any input.
  // This is used by pages where `hideNodesMatching` is only available asynchronously.
  loading?: boolean;
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

export type GraphDataState = {
  graphAssetKeys: AssetKey[];
  allAssetKeys: AssetKey[];
  assetGraphData: GraphData | null;
};
const INITIAL_STATE: GraphDataState = {
  graphAssetKeys: [],
  allAssetKeys: [],
  assetGraphData: null,
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

  const [state, setState] = useState<GraphDataState>(INITIAL_STATE);

  const {kinds, hideEdgesToNodesOutsideQuery} = options;

  const [graphDataLoading, setGraphDataLoading] = useState(true);

  const lastProcessedRequestRef = useRef(0);
  const currentRequestRef = useRef(0);

  useEffect(() => {
    if (options.loading) {
      return;
    }
    const requestId = ++currentRequestRef.current;
    setGraphDataLoading(true);
    computeGraphData({
      repoFilteredNodes,
      graphQueryItems,
      opsQuery,
      kinds,
      hideEdgesToNodesOutsideQuery,
      flagAssetSelectionSyntax: featureEnabled(FeatureFlag.flagAssetSelectionSyntax),
    })?.then((data) => {
      if (lastProcessedRequestRef.current < requestId) {
        lastProcessedRequestRef.current = requestId;
        setState(data);
        if (requestId === currentRequestRef.current) {
          setGraphDataLoading(false);
        }
      }
    });
  }, [
    repoFilteredNodes,
    graphQueryItems,
    opsQuery,
    kinds,
    hideEdgesToNodesOutsideQuery,
    options.loading,
  ]);

  const loading = fetchResult.loading || graphDataLoading;
  useBlockTraceUntilTrue('useAssetGraphData', !loading);
  return {
    loading,
    fetchResult,
    assetGraphData: state.assetGraphData,
    graphQueryItems,
    graphAssetKeys: state.graphAssetKeys,
    allAssetKeys: state.allAssetKeys,
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

const computeGraphData = throttle(
  indexedDBAsyncMemoize<
    ComputeGraphDataMessageType,
    GraphDataState,
    typeof computeGraphDataWrapper
  >(computeGraphDataWrapper, (props) => {
    return JSON.stringify(props);
  }),
  2000,
  {leading: true},
);

const getWorker = memoize(() => new Worker(new URL('./ComputeGraphData.worker', import.meta.url)));

async function computeGraphDataWrapper(
  props: Omit<ComputeGraphDataMessageType, 'type'>,
): Promise<GraphDataState> {
  if (featureEnabled(FeatureFlag.flagAssetSelectionWorker)) {
    const worker = getWorker();
    return new Promise<GraphDataState>((resolve) => {
      worker.addEventListener('message', (event) => {
        resolve(event.data as GraphDataState);
      });
      const message: ComputeGraphDataMessageType = {
        type: 'computeGraphData',
        ...props,
      };
      worker.postMessage(message);
    });
  }
  return computeGraphDataImpl(props);
}
