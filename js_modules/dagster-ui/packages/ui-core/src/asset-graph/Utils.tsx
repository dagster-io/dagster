import {pathHorizontalDiagonal, pathVerticalDiagonal} from '@vx/shape';
import memoize from 'lodash/memoize';

import {AssetNodeKeyFragment} from './types/AssetNode.types';
import {AssetNodeForGraphQueryFragment} from './types/useAssetGraphData.types';
import {COMMON_COLLATOR} from '../app/Util';
import {
  AssetCheckLiveFragment,
  AssetGraphLiveQuery,
  AssetLatestInfoFragment,
  AssetLatestInfoRunFragment,
  AssetNodeLiveFragment,
  AssetNodeLiveFreshnessInfoFragment,
  AssetNodeLiveMaterializationFragment,
  AssetNodeLiveObservationFragment,
} from '../asset-data/types/AssetLiveDataProvider.types';
import {RunStatus, StaleStatus} from '../graphql/types';

/**
 * IMPORTANT: This file is used by the WebWorker so make sure we don't indirectly import React or anything that relies on window/document
 */

/**
 * IMPORTANT: This file is used by the WebWorker so make sure we don't indirectly import React or anything that relies on window/document
 */

type AssetNode = AssetNodeForGraphQueryFragment;
type AssetKey = AssetNodeKeyFragment;
type AssetLiveNode = AssetNodeLiveFragment;
type AssetLatestInfo = AssetLatestInfoFragment;

export const __ASSET_JOB_PREFIX = '__ASSET_JOB';

export function isHiddenAssetGroupJob(jobName: string) {
  return jobName.startsWith(__ASSET_JOB_PREFIX);
}

// IMPORTANT: We use this, rather than AssetNode.id throughout this file because
// the GraphQL interface exposes dependencyKeys, not dependencyIds. We also need
// ways to "build" GraphId's locally, they can't always be server-provided.
//
// This value is NOT the same as AssetNode.id values provided by the server,
// because JSON.stringify's whitespace behavior is different than Python's.
//
export type GraphId = string;
export const toGraphId = (key: {path: string[]}): GraphId => JSON.stringify(key.path);
export const fromGraphId = (graphId: GraphId): AssetNodeKeyFragment => ({
  path: JSON.parse(graphId),
  __typename: 'AssetKey',
});

export interface GraphNode {
  id: GraphId;
  assetKey: AssetKey;
  definition: AssetNode;
}

export interface GraphData {
  nodes: {[assetId: GraphId]: GraphNode};
  downstream: {[assetId: GraphId]: {[childAssetId: GraphId]: boolean}};
  upstream: {[assetId: GraphId]: {[parentAssetId: GraphId]: boolean}};
  expandedGroups?: string[];
}

export const buildGraphData = (assetNodes: AssetNode[]) => {
  const data: GraphData = {
    nodes: {},
    downstream: {},
    upstream: {},
  };

  const addEdge = (upstreamGraphId: string, downstreamGraphId: string) => {
    if (upstreamGraphId === downstreamGraphId) {
      // Skip add edges for self-dependencies (eg: assets relying on older partitions of themselves)
      return;
    }
    data.downstream[upstreamGraphId] = {
      ...(data.downstream[upstreamGraphId] || {}),
      [downstreamGraphId]: true,
    };
    data.upstream[downstreamGraphId] = {
      ...(data.upstream[downstreamGraphId] || {}),
      [upstreamGraphId]: true,
    };
  };

  assetNodes.forEach((definition: AssetNode) => {
    const id = toGraphId(definition.assetKey);
    definition.dependencyKeys.forEach((key) => {
      addEdge(toGraphId(key), id);
    });
    definition.dependedByKeys.forEach((key) => {
      addEdge(id, toGraphId(key));
    });

    data.nodes[id] = {
      id,
      assetKey: definition.assetKey,
      definition,
    };
  });

  return data;
};

export const nodeDependsOnSelf = (node: GraphNode) => {
  const id = toGraphId(node.assetKey);
  return node.definition.dependedByKeys.some((d) => toGraphId(d) === id);
};

export const graphHasCycles = (graphData: GraphData) => {
  const nodes = new Set(Object.keys(graphData.nodes));
  const search = (stack: string[], node: string): boolean => {
    if (stack.indexOf(node) !== -1) {
      return true;
    }
    if (nodes.delete(node) === true) {
      const nextStack = stack.concat(node);
      return Object.keys(graphData.downstream[node] || {}).some((nextNode) =>
        search(nextStack, nextNode),
      );
    }
    return false;
  };
  let hasCycles = false;
  while (nodes.size !== 0 && !hasCycles) {
    hasCycles = search([], nodes.values().next().value);
  }
  return hasCycles;
};

export const buildSVGPathHorizontal = pathHorizontalDiagonal({
  source: (s: any) => s.source,
  target: (s: any) => s.target,
  x: (s: any) => s.x,
  y: (s: any) => s.y,
});
export const buildSVGPathVertical = pathVerticalDiagonal({
  source: (s: any) => s.source,
  target: (s: any) => s.target,
  x: (s: any) => s.x,
  y: (s: any) => s.y,
});

export interface LiveDataForNode {
  stepKey: string;
  unstartedRunIds: string[]; // run in progress and step not started
  inProgressRunIds: string[]; // run in progress and step in progress
  runWhichFailedToMaterialize: AssetLatestInfoRunFragment | null;
  lastMaterialization: AssetNodeLiveMaterializationFragment | null;
  lastMaterializationRunStatus: RunStatus | null; // only available if runWhichFailedToMaterialize is null
  freshnessInfo: AssetNodeLiveFreshnessInfoFragment | null;
  lastObservation: AssetNodeLiveObservationFragment | null;
  staleStatus: StaleStatus | null;
  staleCauses: AssetGraphLiveQuery['assetNodes'][0]['staleCauses'];
  assetChecks: AssetCheckLiveFragment[];
  partitionStats: {
    numMaterialized: number;
    numMaterializing: number;
    numPartitions: number;
    numFailed: number;
  } | null;
  opNames: string[];
}

export const MISSING_LIVE_DATA: LiveDataForNode = {
  unstartedRunIds: [],
  inProgressRunIds: [],
  runWhichFailedToMaterialize: null,
  freshnessInfo: null,
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: null,
  partitionStats: null,
  staleStatus: null,
  staleCauses: [],
  assetChecks: [],
  opNames: [],
  stepKey: '',
};

export interface LiveData {
  [assetId: GraphId]: LiveDataForNode;
}

export const buildLiveData = ({
  assetNodes,
  assetsLatestInfo,
}: Pick<AssetGraphLiveQuery, 'assetNodes' | 'assetsLatestInfo'>) => {
  const data: LiveData = {};

  for (const liveNode of assetNodes) {
    const graphId = toGraphId(liveNode.assetKey);
    const assetLatestInfo = assetsLatestInfo.find(
      (r) => JSON.stringify(r.assetKey) === JSON.stringify(liveNode.assetKey),
    );

    data[graphId] = buildLiveDataForNode(liveNode, assetLatestInfo);
  }

  return data;
};

export const buildLiveDataForNode = (
  assetNode: AssetLiveNode,
  assetLatestInfo?: AssetLatestInfo,
): LiveDataForNode => {
  const lastMaterialization = assetNode.assetMaterializations[0] || null;
  const lastObservation = assetNode.assetObservations[0] || null;
  const latestRunForAsset = assetLatestInfo?.latestRun ? assetLatestInfo.latestRun : null;

  const runWhichFailedToMaterialize =
    (latestRunForAsset?.status === 'FAILURE' &&
      (!lastMaterialization || lastMaterialization.runId !== latestRunForAsset?.id) &&
      latestRunForAsset) ||
    null;

  return {
    lastMaterialization,
    lastMaterializationRunStatus:
      latestRunForAsset && lastMaterialization?.runId === latestRunForAsset?.id
        ? latestRunForAsset.status
        : null,
    lastObservation,
    assetChecks:
      assetNode.assetChecksOrError.__typename === 'AssetChecks'
        ? assetNode.assetChecksOrError.checks
        : [],
    staleStatus: assetNode.staleStatus,
    staleCauses: assetNode.staleCauses,
    stepKey: stepKeyForAsset(assetNode),
    freshnessInfo: assetNode.freshnessInfo,
    inProgressRunIds: assetLatestInfo?.inProgressRunIds || [],
    unstartedRunIds: assetLatestInfo?.unstartedRunIds || [],
    partitionStats: assetNode.partitionStats || null,
    runWhichFailedToMaterialize,
    opNames: assetNode.opNames,
  };
};

export function tokenForAssetKey(key: {path: string[]}) {
  return key.path.join('/');
}

export function tokenToAssetKey(token: string) {
  return {path: token.split('/')};
}

export function displayNameForAssetKey(key: {path: string[]}) {
  return key.path.join(' / ');
}

export function sortAssetKeys(a: {path: string[]}, b: {path: string[]}) {
  return COMMON_COLLATOR.compare(displayNameForAssetKey(a), displayNameForAssetKey(b));
}

export function stepKeyForAsset(definition: {opNames: string[]}) {
  // Used for linking to the run with this step highlighted. We only support highlighting
  // a single step, so just use the first one.
  const firstOp = definition.opNames.length ? definition.opNames[0] : null;
  return firstOp || '';
}

export const itemWithAssetKey = (key: {path: string[]}) => {
  const token = tokenForAssetKey(key);
  return (asset: {assetKey: {path: string[]}}) => tokenForAssetKey(asset.assetKey) === token;
};

export const isGroupId = (str: string) => /^[^@:]+@[^@:]+:.+$/.test(str);

export const groupIdForNode = (node: GraphNode) =>
  [
    node.definition.repository.name,
    '@',
    node.definition.repository.location.name,
    ':',
    node.definition.groupName,
  ].join('');

// Inclusive
export const getUpstreamNodes = memoize(
  (assetKey: AssetNodeKeyFragment, graphData: GraphData): AssetNodeKeyFragment[] => {
    const upstream = Object.keys(graphData.upstream[toGraphId(assetKey)] || {});
    const currentUpstream = upstream.map((graphId) => fromGraphId(graphId));
    return [
      assetKey,
      ...currentUpstream,
      ...currentUpstream.map((graphId) => getUpstreamNodes(graphId, graphData)).flat(),
    ].filter(
      (key, index, arr) =>
        // Filter out non uniques
        arr.findIndex((key2) => JSON.stringify(key2) === JSON.stringify(key)) === index,
    );
  },
  (key, data) => JSON.stringify({key, data}),
);
