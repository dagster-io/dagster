import {gql} from '@apollo/client';
import {pathVerticalDiagonal} from '@vx/shape';

import {AssetNodeDefinitionFragment} from '../assets/types/AssetNodeDefinitionFragment';

import {AssetGraphLiveQuery_assetNodes_assetMaterializations} from './types/AssetGraphLiveQuery';
import {
  AssetGraphQuery_assetNodes,
  AssetGraphQuery_assetNodes_assetKey,
} from './types/AssetGraphQuery';
import {AssetNodeLiveFragment} from './types/AssetNodeLiveFragment';
import {
  RepositoryLiveFragment,
  RepositoryLiveFragment_latestRunByStep_JobRunsCount,
  RepositoryLiveFragment_latestRunByStep_LatestRun_run,
} from './types/RepositoryLiveFragment';

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
export const isSourceAsset = (node: {jobNames: string[]; opName: string | null}) => {
  return node.jobNames.length === 0 && !node.opName;
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

export type Status = 'good' | 'old' | 'none' | 'unknown';

export interface LiveDataForNode {
  computeStatus: Status;
  unstartedRunIds: string[]; // run in progress and step not started
  inProgressRunIds: string[]; // run in progress and step in progress
  runsSinceMaterialization: RepositoryLiveFragment_latestRunByStep_JobRunsCount | null;
  runWhichFailedToMaterialize: RepositoryLiveFragment_latestRunByStep_LatestRun_run | null;
  lastMaterialization: AssetGraphLiveQuery_assetNodes_assetMaterializations | null;
  lastChanged: number;
}
export interface LiveData {
  [assetId: GraphId]: LiveDataForNode;
}

export const buildLiveData = (
  graph: GraphData,
  nodes: AssetNodeLiveFragment[],
  repos: RepositoryLiveFragment[],
) => {
  const data: LiveData = {};

  for (const liveNode of nodes) {
    const graphId = toGraphId(liveNode.assetKey);
    const graphNode = graph.nodes[graphId];
    if (!graphNode) {
      console.warn(`buildLiveData could not find the graph node matching ${graphId}`);
      continue;
    }
    const lastMaterialization = liveNode.assetMaterializations[0] || null;
    const lastChanged = Number(lastMaterialization?.timestamp || 0) / 1000;
    const isPartitioned = graphNode.definition.partitionDefinition;
    const repo = repos.find((r) => r.id === liveNode.repository.id);

    const runs = repo?.inProgressRunsByStep.find((r) => r.stepKey === liveNode.opName);
    const info = repo?.latestRunByStep.find((r) => r.stepKey === liveNode.opName);

    const runsSinceMaterialization = info?.__typename === 'JobRunsCount' ? info : null;
    const latestRunForStepKey = info?.__typename === 'LatestRun' ? info.run : null;

    const runWhichFailedToMaterialize =
      (!runsSinceMaterialization &&
        latestRunForStepKey?.status === 'FAILURE' &&
        (!lastMaterialization || lastMaterialization.runId !== latestRunForStepKey?.id) &&
        latestRunForStepKey) ||
      null;

    data[graphId] = {
      lastChanged,
      lastMaterialization,
      inProgressRunIds: runs?.inProgressRuns.map((r) => r.id) || [],
      unstartedRunIds: runs?.unstartedRuns.map((r) => r.id) || [],
      runsSinceMaterialization,
      runWhichFailedToMaterialize,
      computeStatus: isSourceAsset(graphNode.definition)
        ? 'good' // foreign nodes are always considered up-to-date
        : isPartitioned
        ? // partitioned nodes are not supported, need to compare materializations
          // of the same partition key and the API does not make fetching this easy
          'none'
        : lastMaterialization
        ? 'unknown' // resolve to 'good' or 'old' by looking upstream
        : 'none',
    };
  }

  for (const liveNodeId of Object.keys(data)) {
    data[liveNodeId].computeStatus = findComputeStatusForId(data, graph.upstream, liveNodeId);
  }

  return data;
};

function findComputeStatusForId(
  data: LiveData,
  upstream: {[assetId: string]: {[upstreamAssetId: string]: boolean}},
  assetId: string,
): Status {
  if (!data[assetId]) {
    // Currently compute status assumes foreign nodes are up to date
    // and only shows "upstream changed" for upstreams in the same job
    return 'good';
  }
  const ts = data[assetId].lastChanged;
  const upstreamIds = Object.keys(upstream[assetId] || {});
  if (data[assetId].computeStatus !== 'unknown') {
    return data[assetId].computeStatus;
  }

  return upstreamIds.some((uid) => data[uid]?.lastChanged > ts)
    ? 'old'
    : upstreamIds.some((uid) => findComputeStatusForId(data, upstream, uid) !== 'good')
    ? 'old'
    : 'good';
}

export function tokenForAssetKey(key: {path: string[]}) {
  return key.path.join('>');
}

export function displayNameForAssetKey(key: {path: string[]}) {
  return key.path.join(' > ');
}

export const IN_PROGRESS_RUNS_FRAGMENT = gql`
  fragment InProgressRunsFragment on InProgressRunsByStep {
    stepKey
    unstartedRuns {
      id
    }
    inProgressRuns {
      id
    }
  }
`;

export const LAST_RUNS_WARNINGS_FRAGMENT = gql`
  fragment LastRunsWarningsFragment on RunStatsByStep {
    __typename
    ... on LatestRun {
      stepKey
      run {
        id
        status
      }
    }
    ... on JobRunsCount {
      stepKey
      jobNames
      count
      sinceLatestMaterialization
    }
  }
`;

export const REPOSITORY_LIVE_FRAGMENT = gql`
  fragment RepositoryLiveFragment on Repository {
    id
    name
    location {
      id
      name
    }
    inProgressRunsByStep {
      ...InProgressRunsFragment
    }
    latestRunByStep {
      __typename
      ...LastRunsWarningsFragment
    }
  }
  ${IN_PROGRESS_RUNS_FRAGMENT}
  ${LAST_RUNS_WARNINGS_FRAGMENT}
`;
