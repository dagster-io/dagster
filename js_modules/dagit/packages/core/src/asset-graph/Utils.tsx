import {gql} from '@apollo/client';
import {pathVerticalDiagonal} from '@vx/shape';
import uniq from 'lodash/uniq';

import {AssetNodeDefinitionFragment} from '../assets/types/AssetNodeDefinitionFragment';

import {
  AssetGraphLiveQuery_assetsLiveInfo,
  AssetGraphLiveQuery_assetNodes_assetMaterializations,
} from './types/AssetGraphLiveQuery';
import {
  AssetGraphQuery_assetNodes,
  AssetGraphQuery_assetNodes_assetKey,
} from './types/AssetGraphQuery';
import {AssetNodeLiveFragment} from './types/AssetNodeLiveFragment';
import {
  RepositoryLiveFragment,
  RepositoryLiveFragment_latestRunByStep_run,
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
export const isSourceAsset = (node: {jobNames: string[]; opNames: string[]}) => {
  return node.jobNames.length === 0 && !node.opNames.length;
};

export function identifyBundles(assetIds: string[]) {
  const pathPrefixes: {[prefixId: string]: string[]} = {};

  for (const assetId of assetIds) {
    const assetKeyPath = JSON.parse(assetId);

    for (let ii = 1; ii < assetKeyPath.length; ii++) {
      const prefix = assetKeyPath.slice(0, ii);
      const key = JSON.stringify(prefix);
      pathPrefixes[key] = pathPrefixes[key] || [];
      pathPrefixes[key].push(assetId);
    }
  }

  for (const key of Object.keys(pathPrefixes)) {
    if (pathPrefixes[key].length <= 1) {
      delete pathPrefixes[key];
    }
  }

  const finalBundlePrefixes: {[prefixId: string]: string[]} = {};
  const finalBundleIdForNodeId: {[id: string]: string} = {};

  // Sort the prefix keys by length descending and iterate from the deepest folders first.
  // Dedupe asset keys and replace asset keys we've already seen with the (deeper) folder
  // they are within. This gets us "multi layer folders" of nodes.

  // Turn this:
  // {
  //  "s3": [["s3", "collect"], ["s3", "prod", "a"], ["s3", "prod", "b"]],
  //  "s3/prod": ["s3", "prod", "a"], ["s3", "prod", "b"]
  // }

  // Into this:
  // {
  //  "s3/prod": ["s3", "prod", "a"], ["s3", "prod", "b"]
  //  "s3": [["s3", "collect"], ["s3", "prod"]],
  // }

  for (const prefixId of Object.keys(pathPrefixes).sort((a, b) => b.length - a.length)) {
    const contents = uniq(
      pathPrefixes[prefixId].map((p) =>
        finalBundleIdForNodeId[p] ? finalBundleIdForNodeId[p] : p,
      ),
    );
    if (contents.length === 1 && finalBundlePrefixes[contents[0]]) {
      // If this bundle contains exactly one bundle, no need to show both outlines.
      // Just show the inner one. eg: a > b > asset1, a > b > asset2, just show a > b.
      continue;
    }
    finalBundlePrefixes[prefixId] = contents;
    finalBundlePrefixes[prefixId].forEach((id) => (finalBundleIdForNodeId[id] = prefixId));
  }
  return finalBundlePrefixes;
}

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
  runWhichFailedToMaterialize: RepositoryLiveFragment_latestRunByStep_run | null;
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
  assetsLiveInfo: AssetGraphLiveQuery_assetsLiveInfo[],
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

    const assetLiveRuns = assetsLiveInfo.find(
      (r) => JSON.stringify(r.assetKey) === JSON.stringify(liveNode.assetKey),
    );
    const info = repo?.latestRunByStep.find((r) => liveNode.opNames.includes(r.stepKey));

    const latestRunForStepKey = info?.__typename === 'LatestRun' ? info.run : null;

    const runWhichFailedToMaterialize =
      (latestRunForStepKey?.status === 'FAILURE' &&
        (!lastMaterialization || lastMaterialization.runId !== latestRunForStepKey?.id) &&
        latestRunForStepKey) ||
      null;

    data[graphId] = {
      lastChanged,
      lastMaterialization,
      inProgressRunIds: assetLiveRuns?.inProgressRunIds || [],
      unstartedRunIds: assetLiveRuns?.unstartedRunIds || [],
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
  return key.path.join('/');
}

export function displayNameForAssetKey(key: {path: string[]}) {
  return key.path.join(' / ');
}

export const LAST_RUNS_WARNINGS_FRAGMENT = gql`
  fragment LastRunsWarningsFragment on LatestRun {
    stepKey
    run {
      id
      status
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
    latestRunByStep {
      __typename
      ...LastRunsWarningsFragment
    }
  }
  ${LAST_RUNS_WARNINGS_FRAGMENT}
`;
