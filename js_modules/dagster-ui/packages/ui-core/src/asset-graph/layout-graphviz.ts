import {Graphviz} from '@hpcc-js/wasm/graphviz';

import {IBounds} from '../graph/common';

import {GraphData, GraphNode, groupIdForNode, isGroupId} from './Utils';
import {
  LayoutAssetGraphOptions,
  AssetGraphLayout,
  GroupLayout,
  AssetLayout,
  AssetLayoutEdge,
} from './layout';

const MARGIN = 100;

let graphviz: any;

export const layoutAssetGraphGraphviz = async (
  graphData: GraphData,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  opts: LayoutAssetGraphOptions,
): Promise<AssetGraphLayout> => {
  graphviz = graphviz || (await Graphviz.load());

  const shouldRender = (node?: GraphNode) => node;
  const renderedNodes = Object.values(graphData.nodes).filter(shouldRender);
  const expandedGroups = graphData.expandedGroups || [];

  // Identify all the groups
  const groups: {[id: string]: GroupLayout} = {};

  for (const node of renderedNodes) {
    if (node.definition.groupName) {
      const id = groupIdForNode(node);
      groups[id] = groups[id] || {
        id,
        expanded: expandedGroups.includes(id),
        groupName: node.definition.groupName,
        repositoryName: node.definition.repository.name,
        repositoryLocationName: node.definition.repository.location.name,
        bounds: {x: 0, y: 0, width: 0, height: 0},
      };
    }
  }
  const groupsPresent = Object.keys(groups).length > 1;

  // Add all the nodes inside expanded groups to the graph
  let dotIdMax = 0;
  const dotSubgraphs: {[name: string]: string} = {};
  const dotIds: {[dagsterId: string]: string} = {};
  const dagsterIds: {[dotIds: string]: string} = {};
  const dotId = (dagsterId: string): string => {
    if (dotIds[dagsterId]) {
      return dotIds[dagsterId]!;
    }
    const id = `n${dotIdMax++}`;
    dotIds[dagsterId] = id;
    dagsterIds[id] = dagsterId;
    return id;
  };
  let dotRoot = '';

  // Add all the collapsed group boxes to the graph
  if (groupsPresent) {
    Object.keys(groups).forEach((groupId) => {
      if (!expandedGroups.includes(groupId)) {
        dotRoot += `${dotId(groupId)} [width=2.7 height=1.2];\n`;
      }
    });
  }

  renderedNodes.forEach((node) => {
    const groupId = groupIdForNode(node);
    const d = getAssetNodeDimensions(node.definition);

    if (expandedGroups.includes(groupId)) {
      dotSubgraphs[groupId] = dotSubgraphs[groupId] || '';
      dotSubgraphs[groupId] += `${dotId(node.id)} [width=${d.width / 100} height=${
        d.height / 100
      }];`;
    } else if (!groupsPresent) {
      dotRoot += `${dotId(node.id)} [width=${d.width / 100} height=${d.height / 100}];`;
    }
  });

  const linksToAssetsOutsideGraphedSet: {[id: string]: true} = {};
  const groupIdForAssetId = Object.fromEntries(
    Object.entries(graphData.nodes).map(([id, node]) => [id, groupIdForNode(node)]),
  );

  // Add the edges to the graph, and accumulate a set of "foreign nodes" (for which
  // we have an inbound/outbound edge, but we don't have the `node` in the graphData).
  const renderedEdges: [string, string][] = [];

  Object.entries(graphData.downstream).forEach(([upstreamId, graphDataDownstream]) => {
    const downstreamIds = Object.keys(graphDataDownstream);
    downstreamIds.forEach((downstreamId) => {
      if (
        !shouldRender(graphData.nodes[downstreamId]) &&
        !shouldRender(graphData.nodes[upstreamId])
      ) {
        return;
      }
      let v = upstreamId;
      let w = downstreamId;

      const wGroup = groupIdForAssetId[downstreamId];
      if (groupsPresent && wGroup && !expandedGroups.includes(wGroup)) {
        w = wGroup;
      }
      const vGroup = groupIdForAssetId[upstreamId];
      if (groupsPresent && vGroup && !expandedGroups.includes(vGroup)) {
        v = vGroup;
      }
      if (v === w) {
        return;
      }

      dotRoot += `${dotId(v)} -> ${dotId(w)};\n`;
      renderedEdges.push([v, w]);

      if (!shouldRender(graphData.nodes[downstreamId])) {
        linksToAssetsOutsideGraphedSet[downstreamId] = true;
      } else if (!shouldRender(graphData.nodes[upstreamId])) {
        linksToAssetsOutsideGraphedSet[upstreamId] = true;
      }
    });
  });

  // Add all the link nodes to the graph
  Object.keys(linksToAssetsOutsideGraphedSet).forEach((id) => {
    // const path = JSON.parse(id);
    // const label = path[path.length - 1] || '';
    dotRoot += `${dotId(id)};\n`;
  });

  const graphdot = `digraph G {
    rankdir="LR";
    ranksep=1.5;
    nodesep=0.3;
    node [shape=box fixedsize=true];
    edge [style="invis"]
    ${dotRoot}

    ${Object.entries(dotSubgraphs)
      .map(
        ([k, text]) => `subgraph cluster_${dotId(k)} {
          label="a\\na\\na";
          margin=20;
         ${text}
      }`,
      )
      .join('\n\n')}
  }`;

  console.log(graphdot);
  const graphjson = graphviz.dot(graphdot, 'json0' as any);
  const graphobjects = Object.fromEntries(
    JSON.parse(graphjson).objects.map((o: any) => [
      o.name,
      o.name.startsWith('cluster_') ? o.bb : `${o.pos},${o.width},${o.height}`,
    ]),
  );

  console.log(graphobjects);
  let maxWidth = 1;
  let maxHeight = 1;

  const nodes: {[id: string]: AssetLayout} = {};
  Object.entries(graphobjects).forEach(([dotid, pos]) => {
    const id = dagsterIds[dotid.replace('cluster_', '')]!;
    const [x, y, _w, _h] = pos.split(',').map(Number);
    const w = dotid.startsWith('cluster') ? _w : _w * 100;
    const h = dotid.startsWith('cluster') ? _h : _h * 100;
    const bounds = {
      x,
      y,
      width: w,
      height: h,
    };
    if (!isGroupId(id)) {
      nodes[id] = {id, bounds};
    } else if (!expandedGroups.includes(id)) {
      const group = groups[id]!;
      group.bounds = bounds;
    }

    maxWidth = Math.max(maxWidth, x);
    maxHeight = Math.max(maxHeight, y);
  });

  // Apply bounds to the groups based on the nodes inside them
  if (groupsPresent) {
    for (const node of renderedNodes) {
      const nodeLayout = nodes[node.id];
      if (nodeLayout && node.definition.groupName) {
        const groupId = groupIdForNode(node);
        const group = groups[groupId]!;
        group.bounds =
          group.bounds.width === 0
            ? nodeLayout.bounds
            : extendBounds(group.bounds, nodeLayout.bounds);
      }
    }
    for (const group of Object.values(groups)) {
      if (group.expanded) {
        group.bounds = padBounds(group.bounds, {x: 15, top: 65, bottom: -15});
      }
    }
  }

  const edges: AssetLayoutEdge[] = [];

  renderedEdges.forEach(([vid, wid]) => {
    const v = nodes[vid]?.bounds || groups[vid]?.bounds;
    const w = nodes[wid]?.bounds || groups[vid]?.bounds;
    if (!v || !w) {
      return;
    }
    // Ignore the coordinates from dagre and use the top left + bottom left of the
    edges.push({
      from: {x: v.x + w.width, y: v.y + v.height / 2},
      fromId: vid,
      to: {x: w.x, y: w.y + v.height / 2},
      toId: wid,
    });
  });

  return {
    nodes,
    edges,
    width: maxWidth + MARGIN,
    height: maxHeight + MARGIN,
    groups: groupsPresent ? groups : {},
  };
};

export const ASSET_LINK_NAME_MAX_LENGTH = 10;

export const getAssetLinkDimensions = (label: string, opts: LayoutAssetGraphOptions) => {
  return opts.horizontalDAGs
    ? {width: 32 + 8 * Math.min(ASSET_LINK_NAME_MAX_LENGTH, label.length), height: 90}
    : {width: 106, height: 90};
};

export const padBounds = (a: IBounds, padding: {x: number; top: number; bottom: number}) => {
  return {
    x: a.x - padding.x,
    y: a.y - padding.top,
    width: a.width + padding.x * 2,
    height: a.height + padding.top + padding.bottom,
  };
};

export const extendBounds = (a: IBounds, b: IBounds) => {
  const xmin = Math.min(a.x, b.x);
  const ymin = Math.min(a.y, b.y);
  const xmax = Math.max(a.x + a.width, b.x + b.width);
  const ymax = Math.max(a.y + a.height, b.y + b.height);
  return {x: xmin, y: ymin, width: xmax - xmin, height: ymax - ymin};
};

export const ASSET_NODE_NAME_MAX_LENGTH = 28;

export const getAssetNodeDimensions = (def: {
  assetKey: {path: string[]};
  opNames: string[];
  isSource: boolean;
  isObservable: boolean;
  isPartitioned: boolean;
  graphName: string | null;
  description?: string | null;
  computeKind: string | null;
}) => {
  const width = 265;

  let height = 100; // top tags area + name + description

  if (def.isSource && def.isObservable) {
    height += 30; // status row
  } else if (def.isSource) {
    height += 0; // no status row
  } else {
    height += 26; // status row
    if (def.isPartitioned) {
      height += 40;
    }
  }

  height += 30; // tags beneath

  return {width, height};
};
