import keyBy from 'lodash/keyBy';
import memoize from 'lodash/memoize';
import reject from 'lodash/reject';
import {useEffect, useLayoutEffect, useMemo, useRef, useState} from 'react';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';
import {useAssetGraphSupplementaryData} from 'shared/asset-graph/useAssetGraphSupplementaryData.oss';
import {Worker} from 'shared/workers/Worker.oss';

import {ASSET_NODE_FRAGMENT} from './AssetNode';
import {GraphData, buildGraphData as buildGraphDataImpl, tokenForAssetKey} from './Utils';
import {gql} from '../apollo-client';
import {computeGraphData as computeGraphDataImpl} from './ComputeGraphData';
import {BuildGraphDataMessageType, ComputeGraphDataMessageType} from './ComputeGraphData.types';
import {throttleLatest} from './throttleLatest';
import {featureEnabled} from '../app/Flags';
import {
  AssetGraphQuery,
  AssetGraphQueryVariables,
  AssetGraphQueryVersion,
  AssetNodeForGraphQueryFragment,
} from './types/useAssetGraphData.types';
import {GraphQueryItem} from '../app/GraphQueryImpl';
import {indexedDBAsyncMemoize} from '../app/Util';
import {usePrefixedCacheKey} from '../app/usePrefixedCacheKey';
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
  const queryItems = useMemo(
    () => (nodes ? buildGraphQueryItems(nodes) : []).map(({node}) => node),
    [nodes],
  );

  const [fullAssetGraphData, setFullAssetGraphData] = useState<GraphData | null>(null);
  useBlockTraceUntilTrue('FullAssetGraphData', !!fullAssetGraphData);

  const lastProcessedRequestRef = useRef(0);
  const currentRequestRef = useRef(0);

  useEffect(() => {
    if (options.loading) {
      return;
    }
    const requestId = ++currentRequestRef.current;
    buildGraphData({
      nodes: queryItems,
    })
      ?.then((data) => {
        if (lastProcessedRequestRef.current < requestId) {
          lastProcessedRequestRef.current = requestId;
          setFullAssetGraphData(data);
        }
      })
      .catch((e) => {
        // buildGraphData is throttled and rejects promises when another call is made before the throttle delay.
        console.warn(e);
      });
  }, [options.loading, queryItems]);

  return {fullAssetGraphData, loading: !fetchResult.data || fetchResult.loading || options.loading};
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

  const computeGraphData = useMemo(() => {
    return throttleLatest(
      indexedDBAsyncMemoize<
        Omit<ComputeGraphDataMessageType, 'id' | 'type'>,
        GraphDataState,
        typeof computeGraphDataWrapper
      >(computeGraphDataWrapper, (props) => {
        return JSON.stringify(props);
      }),
      2000,
    );
  }, []);

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

  const {loading: supplementaryDataLoading, data: supplementaryData} =
    useAssetGraphSupplementaryData(opsQuery);

  useLayoutEffect(() => {
    if (options.loading || supplementaryDataLoading) {
      return;
    }

    const requestId = ++currentRequestRef.current;

    if (repoFilteredNodes === undefined || graphQueryItems === undefined) {
      lastProcessedRequestRef.current = requestId;
      setState({allAssetKeys: [], graphAssetKeys: [], assetGraphData: null});
      return;
    }

    setGraphDataLoading(true);
    computeGraphData({
      repoFilteredNodes,
      graphQueryItems,
      opsQuery,
      kinds,
      hideEdgesToNodesOutsideQuery,
      supplementaryData,
    })
      ?.then((data) => {
        if (lastProcessedRequestRef.current < requestId) {
          lastProcessedRequestRef.current = requestId;
          setState(data);
          if (requestId === currentRequestRef.current) {
            setGraphDataLoading(false);
          }
        }
      })
      .catch((e) => {
        // computeGraphData is throttled and rejects promises when another call is made before the throttle delay.
        console.warn(e);
        if (requestId === currentRequestRef.current) {
          setGraphDataLoading(false);
        }
      });
  }, [
    repoFilteredNodes,
    graphQueryItems,
    opsQuery,
    kinds,
    hideEdgesToNodesOutsideQuery,
    options.loading,
    supplementaryData,
    supplementaryDataLoading,
    computeGraphData,
  ]);

  const loading = fetchResult.loading || graphDataLoading || supplementaryDataLoading;
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

const getWorker = memoize(
  (_key: 'computeGraphWorker' | 'buildGraphWorker') =>
    new Worker(new URL('./ComputeGraphData.worker', import.meta.url)),
);

if (typeof jest === 'undefined') {
  // Pre-warm workers
  getWorker('computeGraphWorker');
  getWorker('buildGraphWorker');
}

let _id = 0;
async function computeGraphDataWrapper(
  props: Omit<ComputeGraphDataMessageType, 'id' | 'type'>,
): Promise<GraphDataState> {
  if (featureEnabled(FeatureFlag.flagAssetSelectionWorker)) {
    const worker = getWorker('computeGraphWorker');
    return new Promise<GraphDataState>((resolve) => {
      const id = ++_id;
      const removeMessageListener = worker.onMessage((event: MessageEvent) => {
        const data = event.data as GraphDataState & {id: number};
        if (data.id === id) {
          resolve(data);
          removeMessageListener();
        }
      });
      const message: ComputeGraphDataMessageType = {
        type: 'computeGraphData',
        id,
        ...props,
      };
      worker.postMessage(message);
    });
  }
  return computeGraphDataImpl(props);
}

const buildGraphData = throttleLatest(
  indexedDBAsyncMemoize<BuildGraphDataMessageType, GraphData, typeof buildGraphDataWrapper>(
    buildGraphDataWrapper,
    (props) => {
      return JSON.stringify(props);
    },
  ),
  2000,
);

async function buildGraphDataWrapper(
  props: Omit<BuildGraphDataMessageType, 'id' | 'type'>,
): Promise<GraphData> {
  if (featureEnabled(FeatureFlag.flagAssetSelectionWorker)) {
    const worker = getWorker('buildGraphWorker');
    return new Promise<GraphData>((resolve) => {
      const id = ++_id;
      const removeMessageListener = worker.onMessage((event: MessageEvent) => {
        const data = event.data as GraphData & {id: number};
        if (data.id === id) {
          resolve(data);
          removeMessageListener();
        }
      });
      const message: BuildGraphDataMessageType = {
        type: 'buildGraphData',
        id,
        ...props,
      };
      worker.postMessage(message);
    });
  }
  return buildGraphDataImpl(props.nodes);
}
