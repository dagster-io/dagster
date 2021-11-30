import {pathVerticalDiagonal} from '@vx/shape';
import * as dagre from 'dagre';

import {getNodeDimensions} from './AssetNode';
import {getForeignNodeDimensions} from './ForeignNode';
import {
  AssetGraphLiveQuery,
  AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations,
} from './types/AssetGraphLiveQuery';
import {
  AssetGraphQuery_pipelineOrError_Pipeline_assetNodes,
  AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetKey,
} from './types/AssetGraphQuery';

type AssetNode = AssetGraphQuery_pipelineOrError_Pipeline_assetNodes;
type AssetKey = AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetKey;

export interface Node {
  id: string;
  assetKey: AssetKey;
  definition: AssetNode;
  hidden: boolean;
}
interface LayoutNode {
  id: string;
  x: number;
  y: number;
}
export interface GraphData {
  nodes: {[id: string]: Node};
  downstream: {[upstream: string]: {[downstream: string]: string}};
  upstream: {[downstream: string]: {[upstream: string]: boolean}};
}
interface IPoint {
  x: number;
  y: number;
}
export type IEdge = {
  from: IPoint;
  to: IPoint;
  dashed: boolean;
};

export function assetKeyToString(key: {path: string[]}) {
  return key.path.join('>');
}

export const buildGraphData = (assetNodes: AssetNode[], jobName?: string) => {
  const nodes: {[id: string]: Node} = {};
  const downstream: {[id: string]: {[childAssetId: string]: string}} = {};
  const upstream: {[id: string]: {[parentAssetId: string]: boolean}} = {};

  assetNodes.forEach((definition: AssetNode) => {
    const assetKeyJson = JSON.stringify(definition.assetKey.path);
    definition.dependencies.forEach(({upstreamAsset, inputName}) => {
      const upstreamAssetKeyJson = JSON.stringify(upstreamAsset.assetKey.path);
      downstream[upstreamAssetKeyJson] = {
        ...(downstream[upstreamAssetKeyJson] || {}),
        [assetKeyJson]: inputName,
      };
      upstream[assetKeyJson] = {
        ...(upstream[assetKeyJson] || {}),
        [upstreamAssetKeyJson]: true,
      };
    });
    nodes[assetKeyJson] = {
      id: assetKeyJson,
      assetKey: definition.assetKey,
      hidden: !!jobName && definition.jobName !== jobName,
      definition,
    };
  });

  return {nodes, downstream, upstream};
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

export const layoutGraph = (graphData: GraphData, margin = 100) => {
  const g = new dagre.graphlib.Graph();

  g.setGraph({rankdir: 'TB', marginx: margin, marginy: margin});
  g.setDefaultEdgeLabel(() => ({}));

  Object.values(graphData.nodes)
    .filter((x) => !x.hidden)
    .forEach((node) => {
      g.setNode(node.id, getNodeDimensions(node.definition));
    });
  const foreignNodes = {};
  Object.keys(graphData.downstream).forEach((upstreamId) => {
    const downstreamIds = Object.keys(graphData.downstream[upstreamId]);
    downstreamIds.forEach((downstreamId) => {
      if (graphData.nodes[downstreamId].hidden && graphData.nodes[upstreamId].hidden) {
        return;
      }
      g.setEdge({v: upstreamId, w: downstreamId}, {weight: 1});
      if (!graphData.nodes[downstreamId] || graphData.nodes[downstreamId].hidden) {
        foreignNodes[downstreamId] = true;
      } else if (!graphData.nodes[upstreamId] || graphData.nodes[upstreamId].hidden) {
        foreignNodes[upstreamId] = true;
      }
    });
  });

  Object.keys(foreignNodes).forEach((upstreamId) => {
    g.setNode(upstreamId, getForeignNodeDimensions(upstreamId));
  });

  dagre.layout(g);

  const dagreNodesById: {[id: string]: dagre.Node} = {};
  g.nodes().forEach((id) => {
    const node = g.node(id);
    if (!node) {
      return;
    }
    dagreNodesById[id] = node;
  });

  let maxWidth = 0;
  let maxHeight = 0;
  const nodes: LayoutNode[] = [];
  Object.keys(dagreNodesById).forEach((id) => {
    const dagreNode = dagreNodesById[id];
    nodes.push({
      id,
      x: dagreNode.x - dagreNode.width / 2,
      y: dagreNode.y - dagreNode.height / 2,
    });
    maxWidth = Math.max(maxWidth, dagreNode.x + dagreNode.width / 2);
    maxHeight = Math.max(maxHeight, dagreNode.y + dagreNode.height / 2);
  });

  const edges: IEdge[] = [];
  g.edges().forEach((e) => {
    const points = g.edge(e).points;
    edges.push({
      from: points[0],
      to: points[points.length - 1],
      dashed: false,
    });
  });

  return {
    nodes,
    edges,
    width: maxWidth + margin,
    height: maxHeight + margin,
  };
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
  inProgressRunIds: string[];
  lastMaterialization: AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations;
  lastStepStart: number;
}
export interface LiveData {
  [assetId: string]: LiveDataForNode;
}

export const buildLiveData = (
  graph: ReturnType<typeof buildGraphData>,
  queryResult?: AssetGraphLiveQuery,
) => {
  const data: LiveData = {};

  if (!queryResult) {
    return data;
  }

  const {repositoryOrError, pipelineOrError} = queryResult;

  const nodes = pipelineOrError.__typename === 'Pipeline' ? pipelineOrError.assetNodes : [];
  const inProgressRunsByStep =
    repositoryOrError.__typename === 'Repository' ? repositoryOrError.inProgressRunsByStep : [];

  for (const node of nodes) {
    const lastMaterialization = node.assetMaterializations[0];
    const lastStepStart = lastMaterialization?.materializationEvent.stepStats?.startTime || 0;

    data[node.id] = {
      lastStepStart,
      lastMaterialization,
      inProgressRunIds:
        inProgressRunsByStep.find((r) => r.stepKey === node.opName)?.runs.map((r) => r.runId) || [],
      computeStatus: lastMaterialization ? 'unknown' : 'none',
    };
  }

  for (const asset of nodes) {
    data[asset.id].computeStatus = findComputeStatusForId(data, graph.upstream, asset.id);
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
  const ts = data[assetId].lastStepStart;
  const upstreamIds = Object.keys(upstream[assetId] || {});
  if (data[assetId].computeStatus !== 'unknown') {
    return data[assetId].computeStatus;
  }

  return upstreamIds.some((uid) => data[uid]?.lastStepStart > ts)
    ? 'old'
    : upstreamIds.some((uid) => findComputeStatusForId(data, upstream, uid) !== 'good')
    ? 'old'
    : 'good';
}
