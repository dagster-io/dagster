import {useMemo} from 'react';

import {AssetColumnLineages} from './lineage/useColumnLineageDataForAssets';
import {GraphData, groupIdForNode, toGraphId, tokenForAssetKey} from '../asset-graph/Utils';
import {LayoutAssetGraphOptions} from '../asset-graph/layout';
import {useAssetLayout} from '../graph/asyncGraphLayout';

const LINEAGE_GRAPH_COLUMN_LAYOUT_OPTIONS: LayoutAssetGraphOptions = {
  direction: 'horizontal',
  overrides: {
    nodeHeight: 32,
    nodesep: 0,
    edgesep: 0,
    groupPaddingBottom: -5,
    groupPaddingTop: 68,
    groupRendering: 'always',
  },
};

type Item = {assetGraphId: string; column: string; direction?: 'upstream' | 'downstream'};

export function toColumnGraphId(item: {assetGraphId: string; column: string}) {
  return JSON.stringify({assetGraphId: item.assetGraphId, column: item.column});
}
export function fromColumnGraphId(id: string) {
  return JSON.parse(id) as {assetGraphId: string; column: string};
}

/**
 * This function returns GraphData in which each `node` is a column of an asset and each `group`
 * is an asset, essentially "zooming in" to the asset column level. This is a bit awkward but
 * allows us to reuse the asset layout engine (and all it's caching, async dispatch, etc) for
 * this view.
 */
export function useColumnLineageLayout(
  assetGraphData: GraphData,
  assetGraphId: string,
  column: string,
  columnLineageData: AssetColumnLineages,
) {
  const {columnGraphData, groups} = useMemo(() => {
    const columnGraphData: GraphData = {
      nodes: {},
      downstream: {},
      upstream: {},
    };

    const downstreams = buildReverseEdgeLookupTable(columnLineageData);

    const addEdge = (upstreamId: string, downstreamId: string) => {
      columnGraphData.upstream[downstreamId] = columnGraphData.upstream[downstreamId] || {};
      columnGraphData.upstream[downstreamId]![upstreamId] = true;
      columnGraphData.downstream[upstreamId] = columnGraphData.downstream[upstreamId] || {};
      columnGraphData.downstream[upstreamId]![downstreamId] = true;
    };

    const groups = new Set<string>();
    const queue: Item[] = [{assetGraphId, column}];
    let item: Item | undefined;

    while ((item = queue.pop())) {
      if (!item) {
        continue;
      }
      const id = toColumnGraphId(item);
      const {assetGraphId, column, direction} = item;
      const assetNode = assetGraphData.nodes[assetGraphId];
      if (columnGraphData.nodes[id] || !assetNode) {
        continue; // visited already
      }

      const columnGraphNode = {
        id,
        assetKey: assetNode.assetKey,
        definition: {
          ...assetNode.definition,
          groupName: `${tokenForAssetKey(assetNode.assetKey)}`,
        },
      };
      columnGraphData.nodes[id] = columnGraphNode;
      groups.add(groupIdForNode(columnGraphNode));

      if (!direction || direction === 'upstream') {
        const lineageForColumn = columnLineageData[assetGraphId]?.[column];
        for (const upstream of lineageForColumn?.upstream || []) {
          const upstreamGraphId = toGraphId(upstream.assetKey);
          const upstreamItem: Item = {
            assetGraphId: upstreamGraphId,
            column: upstream.columnName,
            direction: 'upstream',
          };
          if (assetGraphData.nodes[upstreamItem.assetGraphId]) {
            queue.push(upstreamItem);
            addEdge(toColumnGraphId(upstreamItem), id);
          }
        }
      }
      if (!direction || direction === 'downstream') {
        for (const downstreamId of Object.keys(downstreams[id] || {})) {
          const downstreamItem: Item = {
            ...fromColumnGraphId(downstreamId),
            direction: 'downstream',
          };
          if (assetGraphData.nodes[downstreamItem.assetGraphId]) {
            queue.push(downstreamItem);
            addEdge(id, downstreamId);
          }
        }
      }
    }

    return {columnGraphData, groups: Array.from(groups)};
  }, [assetGraphData, column, columnLineageData, assetGraphId]);

  return useAssetLayout(columnGraphData, groups, LINEAGE_GRAPH_COLUMN_LAYOUT_OPTIONS);
}

/**
 * The column lineage data we get from asset metadata only gives us upstreams for each column.
 * To efficiently build graph data we need both upstreams and downstreams for each column.
 * This function visits every node and builds a downstreams lookup table.
 */
function buildReverseEdgeLookupTable(columnLineageData: AssetColumnLineages) {
  const downstreams: {[id: string]: {[id: string]: true}} = {};

  Object.entries(columnLineageData).forEach(([downstreamAssetGraphId, e]) => {
    Object.entries(e || {}).forEach(([downstreamColumnName, {upstream}]) => {
      const downstreamKey = toColumnGraphId({
        assetGraphId: downstreamAssetGraphId,
        column: downstreamColumnName,
      });
      for (const {assetKey, columnName} of upstream) {
        const key = toColumnGraphId({assetGraphId: toGraphId(assetKey), column: columnName});
        downstreams[key] = downstreams[key] || {};
        downstreams[key]![downstreamKey] = true;
      }
    });
  });

  return downstreams;
}
