import {pathVerticalDiagonal} from '@vx/shape';

import {AssetComputeStatus} from '../types/globalTypes';

import {
  AssetGraphLiveQuery_assetsLatestInfo_latestRun,
  AssetGraphLiveQuery_assetNodes_assetMaterializations,
  AssetGraphLiveQuery,
  AssetGraphLiveQuery_assetsLatestInfo,
  AssetGraphLiveQuery_assetNodes,
} from './types/AssetGraphLiveQuery';
import {
  AssetGraphQuery_assetNodes,
  AssetGraphQuery_assetNodes_assetKey,
} from './types/AssetGraphQuery';
type AssetNode = AssetGraphQuery_assetNodes;
type AssetKey = AssetGraphQuery_assetNodes_assetKey;
type AssetLiveNode = AssetGraphLiveQuery_assetNodes;
type AssetLatestInfo = AssetGraphLiveQuery_assetsLatestInfo;

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

export interface GraphNode {
  id: GraphId;
  assetKey: AssetKey;
  definition: AssetNode;
}

export interface GraphData {
  nodes: {[assetId: GraphId]: GraphNode};
  downstream: {[assetId: GraphId]: {[childAssetId: GraphId]: boolean}};
  upstream: {[assetId: GraphId]: {[parentAssetId: GraphId]: boolean}};
}
export const isSourceAsset = (node: {graphName: string | null; opNames: string[]}) => {
  return !node.graphName && !node.opNames.length;
};

export const buildGraphData = (assetNodes: AssetNode[]) => {
  const data: GraphData = {
    nodes: {},
    downstream: {},
    upstream: {},
  };

  const addEdge = (upstreamGraphId: string, downstreamGraphId: string) => {
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
  while (nodes.size !== 0) {
    hasCycles = hasCycles || search([], nodes.values().next().value);
  }
  return hasCycles;
};

export const buildSVGPath = pathVerticalDiagonal({
  source: (s: any) => s.source,
  target: (s: any) => s.target,
  x: (s: any) => s.x,
  y: (s: any) => s.y,
});

export interface LiveDataForNode {
  stepKey: string;
  unstartedRunIds: string[]; // run in progress and step not started
  inProgressRunIds: string[]; // run in progress and step in progress
  runWhichFailedToMaterialize: AssetGraphLiveQuery_assetsLatestInfo_latestRun | null;
  lastMaterialization: AssetGraphLiveQuery_assetNodes_assetMaterializations | null;
  computeStatus: AssetComputeStatus;
}
export interface LiveData {
  [assetId: GraphId]: LiveDataForNode;
}

export interface AssetDefinitionsForLiveData {
  [id: string]: {
    definition: {
      partitionDefinition: string | null;
      jobNames: string[];
      opNames: string[];
    };
  };
}

export const buildLiveData = ({assetNodes, assetsLatestInfo}: AssetGraphLiveQuery) => {
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
  const latestRunForAsset = assetLatestInfo?.latestRun ? assetLatestInfo.latestRun : null;

  const runWhichFailedToMaterialize =
    (latestRunForAsset?.status === 'FAILURE' &&
      (!lastMaterialization || lastMaterialization.runId !== latestRunForAsset?.id) &&
      latestRunForAsset) ||
    null;

  return {
    lastMaterialization,
    stepKey: assetNode.opNames[0],
    inProgressRunIds: assetLatestInfo?.inProgressRunIds || [],
    unstartedRunIds: assetLatestInfo?.unstartedRunIds || [],
    computeStatus: assetLatestInfo?.computeStatus || AssetComputeStatus.NONE,
    runWhichFailedToMaterialize,
  };
};

export function tokenForAssetKey(key: {path: string[]}) {
  return key.path.join('/');
}

export function displayNameForAssetKey(key: {path: string[]}) {
  return key.path.join(' / ');
}
