import {pathVerticalDiagonal} from '@vx/shape';

import {AssetNodeDefinitionFragment} from '../assets/types/AssetNodeDefinitionFragment';

import {
  AssetGraphLiveQuery_assetsLatestInfo,
  AssetGraphLiveQuery_assetsLatestInfo_latestRun,
  AssetGraphLiveQuery_assetNodes_assetMaterializations,
} from './types/AssetGraphLiveQuery';
import {
  AssetGraphQuery_assetNodes,
  AssetGraphQuery_assetNodes_assetKey,
} from './types/AssetGraphQuery';
import {AssetNodeLiveFragment} from './types/AssetNodeLiveFragment';
type AssetNode = AssetGraphQuery_assetNodes;
type AssetKey = AssetGraphQuery_assetNodes_assetKey;

export const __ASSET_GROUP_PREFIX = '__ASSET_GROUP';

export function isAssetGroup(jobName: string) {
  return jobName.startsWith(__ASSET_GROUP_PREFIX);
}

// IMPORTANT: We use this, rather than AssetNode.id throughout this file because
// the GraphQL interface exposes dependencyKeys, not dependencyIds. We also need
// ways to "build" GraphId's locally, they can't always be server-provided.
//
// This value is NOT the same as AssetNode.id values provided by the server,
// because JSON.stringify's whitespace behavior is different than Python's.
//
export type GraphId = string;
export const toGraphId = (key: AssetKey): GraphId => JSON.stringify(key.path);

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
export const isSourceAsset = (node: {jobNames: string[]; opNames: string[]}) => {
  return node.jobNames.length === 0 && !node.opNames.length;
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

export const buildGraphDataFromSingleNode = (assetNode: AssetNodeDefinitionFragment) => {
  const id = toGraphId(assetNode.assetKey);
  const graphData: GraphData = {
    downstream: {
      [id]: {},
    },
    nodes: {
      [id]: {
        id,
        assetKey: assetNode.assetKey,
        definition: {...assetNode, dependencyKeys: [], dependedByKeys: []},
      },
    },
    upstream: {
      [id]: {},
    },
  };

  for (const {asset} of assetNode.dependencies) {
    const depId = toGraphId(asset.assetKey);
    graphData.upstream[id][depId] = true;
    graphData.downstream[depId] = {...graphData.downstream[depId], [id]: true};
    graphData.nodes[depId] = {
      id: depId,
      assetKey: asset.assetKey,
      definition: {...asset, dependencyKeys: [], dependedByKeys: []},
    };
  }
  for (const {asset} of assetNode.dependedBy) {
    const depId = toGraphId(asset.assetKey);
    graphData.upstream[depId] = {...graphData.upstream[depId], [id]: true};
    graphData.downstream[id][depId] = true;
    graphData.nodes[depId] = {
      id: depId,
      assetKey: asset.assetKey,
      definition: {...asset, dependencyKeys: [], dependedByKeys: []},
    };
  }
  return graphData;
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

export type ComputeStatus = 'good' | 'old' | 'none' | 'unknown';

export interface LiveDataForNode {
  unstartedRunIds: string[]; // run in progress and step not started
  inProgressRunIds: string[]; // run in progress and step in progress
  runWhichFailedToMaterialize: AssetGraphLiveQuery_assetsLatestInfo_latestRun | null;
  lastMaterialization: AssetGraphLiveQuery_assetNodes_assetMaterializations | null;
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

export const buildComputeStatusData = (graph: GraphData, liveData: LiveData) => {
  const statuses: {[assetId: string]: ComputeStatus} = {};
  const lastChanged: {[assetId: string]: number} = {};

  for (const [graphId, liveNode] of Object.entries(liveData)) {
    const definition = graph.nodes[graphId]?.definition;
    if (!definition) {
      console.warn(`buildUpstreamChangedData could not find the definition matching ${graphId}`);
      continue;
    }

    lastChanged[graphId] = Number(liveNode.lastMaterialization?.timestamp || 0) / 1000;
    statuses[graphId] = isSourceAsset(definition)
      ? 'good' // foreign nodes are always considered up-to-date
      : definition.partitionDefinition
      ? // partitioned nodes are not supported, need to compare materializations
        // of the same partition key and the API does not make fetching this easy
        'none'
      : liveNode.lastMaterialization
      ? 'unknown' // will resolve to 'good' or 'old' by looking upstream below
      : 'none';
  }

  const fillStatusFor = (assetId: string): ComputeStatus => {
    if (!statuses[assetId]) {
      // Currently compute status assumes foreign nodes are up to date
      // and only shows "upstream changed" for upstreams in the same job
      return 'good';
    }
    if (statuses[assetId] !== 'unknown') {
      return statuses[assetId];
    }

    const upstreamIds = Object.keys(graph.upstream[assetId] || {});

    return upstreamIds.some((upstreamId) => lastChanged[upstreamId] > lastChanged[assetId])
      ? 'old'
      : upstreamIds.some((upstreamId) => fillStatusFor(upstreamId) !== 'good')
      ? 'old'
      : 'good';
  };

  for (const assetId of Object.keys(statuses)) {
    statuses[assetId] = fillStatusFor(assetId);
  }

  return statuses;
};

export const buildLiveData = (
  assets: AssetDefinitionsForLiveData,
  nodes: AssetNodeLiveFragment[],
  assetsLatestInfo: AssetGraphLiveQuery_assetsLatestInfo[],
) => {
  const data: LiveData = {};

  for (const liveNode of nodes) {
    const graphId = toGraphId(liveNode.assetKey);
    const definition = assets[graphId]?.definition;
    if (!definition) {
      console.warn(`buildLiveData could not find the definition matching ${graphId}`);
      continue;
    }
    const lastMaterialization = liveNode.assetMaterializations[0] || null;

    const assetLiveRuns = assetsLatestInfo.find(
      (r) => JSON.stringify(r.assetKey) === JSON.stringify(liveNode.assetKey),
    );

    const latestRunForAsset = assetLiveRuns?.latestRun ? assetLiveRuns.latestRun : null;

    const runWhichFailedToMaterialize =
      (latestRunForAsset?.status === 'FAILURE' &&
        (!lastMaterialization || lastMaterialization.runId !== latestRunForAsset?.id) &&
        latestRunForAsset) ||
      null;

    data[graphId] = {
      lastMaterialization,
      inProgressRunIds: assetLiveRuns?.inProgressRunIds || [],
      unstartedRunIds: assetLiveRuns?.unstartedRunIds || [],
      runWhichFailedToMaterialize,
    };
  }

  return data;
};

export function tokenForAssetKey(key: {path: string[]}) {
  return key.path.join('/');
}

export function displayNameForAssetKey(key: {path: string[]}) {
  return key.path.join(' / ');
}
