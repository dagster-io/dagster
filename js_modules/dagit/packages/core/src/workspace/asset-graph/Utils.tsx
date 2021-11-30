import {pathVerticalDiagonal} from '@vx/shape';
import * as dagre from 'dagre';

import {getNodeDimensions} from './AssetNode';
import {getForeignNodeDimensions} from './ForeignNode';
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
  width: number;
  height: number;
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
  const downstream: {[downstreamId: string]: {[upstreamId: string]: string}} = {};
  const upstream: {[upstreamId: string]: {[downstreamId: string]: boolean}} = {};

  assetNodes.forEach((definition: AssetNode) => {
    const assetKeyJson = JSON.stringify(definition.assetKey.path);
    definition.dependencies.forEach(({asset, inputName}) => {
      const upstreamAssetKeyJson = JSON.stringify(asset.assetKey.path);
      downstream[upstreamAssetKeyJson] = {
        ...(downstream[upstreamAssetKeyJson] || {}),
        [assetKeyJson]: inputName,
      };
      upstream[assetKeyJson] = {
        ...(upstream[assetKeyJson] || {}),
        [upstreamAssetKeyJson]: true,
      };
    });
    definition.dependedBy.forEach(({asset, inputName}) => {
      const downstreamAssetKeyJson = JSON.stringify(asset.assetKey.path);
      upstream[downstreamAssetKeyJson] = {
        ...(upstream[downstreamAssetKeyJson] || {}),
        [assetKeyJson]: true,
      };
      downstream[assetKeyJson] = {
        ...(downstream[assetKeyJson] || {}),
        [downstreamAssetKeyJson]: inputName,
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

export const layoutGraph = (
  graphData: GraphData,
  opts: {margin: number; mini: boolean} = {
    margin: 100,
    mini: false,
  },
) => {
  const g = new dagre.graphlib.Graph();

  g.setGraph({
    rankdir: 'TB',
    marginx: opts.margin,
    marginy: opts.margin,
    nodesep: opts.mini ? 20 : 50,
    edgesep: opts.mini ? 10 : 10,
    ranksep: opts.mini ? 20 : 50,
  });
  g.setDefaultEdgeLabel(() => ({}));

  Object.values(graphData.nodes)
    .filter((x) => !x.hidden)
    .forEach((node) => {
      const {width, height} = getNodeDimensions(node.definition);
      g.setNode(node.id, {width: opts.mini ? 230 : width, height});
    });

  const foreignNodes = {};
  Object.keys(graphData.downstream).forEach((upstreamId) => {
    const downstreamIds = Object.keys(graphData.downstream[upstreamId]);
    downstreamIds.forEach((downstreamId) => {
      if (
        graphData.nodes[downstreamId] &&
        graphData.nodes[downstreamId].hidden &&
        graphData.nodes[upstreamId].hidden
      ) {
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
      width: dagreNode.width,
      height: dagreNode.height,
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
    width: maxWidth + opts.margin,
    height: maxHeight + opts.margin,
  };
};

export const buildSVGPath = pathVerticalDiagonal({
  source: (s: any) => s.source,
  target: (s: any) => s.target,
  x: (s: any) => s.x,
  y: (s: any) => s.y,
});

export function buildGraphComputeStatuses(graphData: GraphData) {
  const timestamps: {[key: string]: number} = {};
  for (const node of Object.values(graphData.nodes)) {
    timestamps[node.id] =
      node.definition.assetMaterializations[0]?.materializationEvent.stepStats?.startTime || 0;
  }
  const upstream: {[key: string]: string[]} = {};
  Object.keys(graphData.downstream).forEach((upstreamId) => {
    const downstreamIds = Object.keys(graphData.downstream[upstreamId]);

    downstreamIds.forEach((downstreamId) => {
      upstream[downstreamId] = upstream[downstreamId] || [];
      upstream[downstreamId].push(upstreamId);
    });
  });

  const statuses: {[key: string]: Status} = {};

  for (const asset of Object.values(graphData.nodes)) {
    if (asset.definition.assetMaterializations.length === 0) {
      statuses[asset.id] = 'none';
    }
  }
  for (const asset of Object.values(graphData.nodes)) {
    const id = JSON.stringify(asset.assetKey.path);
    statuses[id] = findComputeStatusForId(timestamps, statuses, upstream, id);
  }
  return statuses;
}

export type Status = 'good' | 'old' | 'none';

function findComputeStatusForId(
  timestamps: {[key: string]: number},
  statuses: {[key: string]: Status},
  upstream: {[key: string]: string[]},
  id: string,
): Status {
  const ts = timestamps[id];
  const upstreamIds = upstream[id] || [];
  if (id in statuses) {
    return statuses[id];
  }

  statuses[id] = upstreamIds.some((uid) => timestamps[uid] > ts)
    ? 'old'
    : upstreamIds.some(
        (uid) => findComputeStatusForId(timestamps, statuses, upstream, uid) !== 'good',
      )
    ? 'old'
    : 'good';

  return statuses[id];
}
