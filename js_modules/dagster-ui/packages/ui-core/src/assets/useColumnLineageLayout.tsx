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
  },
};

type Item = {assetGraphId: string; column: string};

export function toColumnGraphId(item: {assetGraphId: string; column: string}) {
  return JSON.stringify(item);
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

    const groups = new Set<string>();
    const queue: Item[] = [{assetGraphId, column}];
    let item: Item | undefined;

    const downstreams = buildReverseEdgeLookupTable(columnLineageData);

    while ((item = queue.pop())) {
      if (!item) {
        continue;
      }
      const id = toColumnGraphId(item);
      const {assetGraphId, column} = item;
      const assetGraphNode = assetGraphData.nodes[assetGraphId];
      if (columnGraphData.nodes[id] || !assetGraphNode) {
        continue; // visited already
      }

      columnGraphData.nodes[id] = {
        assetKey: assetGraphNode.assetKey,
        definition: {
          ...assetGraphNode.definition,
          groupName: `${tokenForAssetKey(assetGraphNode.assetKey)}`,
        },
        id,
      };

      const lineageForColumn = columnLineageData[assetGraphId]?.[column];

      for (const upstream of lineageForColumn?.upstream || []) {
        for (const upstreamAssetKey of upstream.assetKeys) {
          const upstreamGraphId = toGraphId(upstreamAssetKey);
          const upstreamItem = {assetGraphId: upstreamGraphId, column: upstream.columnName};
          const upstreamId = toColumnGraphId(upstreamItem);
          queue.push(upstreamItem);
          columnGraphData.upstream[id] = columnGraphData.upstream[id] || {};
          columnGraphData.upstream[id]![upstreamId] = true;
          columnGraphData.downstream[upstreamId] = columnGraphData.downstream[upstreamId] || {};
          columnGraphData.downstream[upstreamId]![id] = true;
        }
      }
      for (const downstreamId of Object.keys(downstreams[id] || {})) {
        queue.push(fromColumnGraphId(downstreamId));
        columnGraphData.downstream[id] = columnGraphData.downstream[id] || {};
        columnGraphData.downstream[id]![downstreamId] = true;
        columnGraphData.upstream[downstreamId] = columnGraphData.upstream[downstreamId] || {};
        columnGraphData.upstream[downstreamId]![id] = true;
      }

      groups.add(groupIdForNode(columnGraphData.nodes[id]!));
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
      for (const {assetKeys, columnName} of upstream) {
        for (const assetKey of assetKeys) {
          const key = toColumnGraphId({assetGraphId: toGraphId(assetKey), column: columnName});
          downstreams[key] = downstreams[key] || {};
          downstreams[key]![downstreamKey] = true;
        }
      }
    });
  });

  return downstreams;
}
