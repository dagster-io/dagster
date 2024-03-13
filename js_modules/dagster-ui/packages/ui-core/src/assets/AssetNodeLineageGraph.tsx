import {Box, Spinner} from '@dagster-io/ui-components';
import {useEffect, useMemo, useRef, useState} from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {
  AssetColumnLineageLocal,
  AssetColumnLineages,
} from './lineage/useColumnLineageDataForAssets';
import {AssetKey, AssetViewParams} from './types';
import {AssetColumnsNode} from '../asset-graph/AssetColumnsNode';
import {AssetEdges} from '../asset-graph/AssetEdges';
import {MINIMAL_SCALE} from '../asset-graph/AssetGraphExplorer';
import {AssetNode, AssetNodeContextMenuWrapper, AssetNodeMinimal} from '../asset-graph/AssetNode';
import {ExpandedGroupNode, GroupOutline} from '../asset-graph/ExpandedGroupNode';
import {AssetNodeLink} from '../asset-graph/ForeignNode';
import {GraphData, GraphNode, groupIdForNode, toGraphId} from '../asset-graph/Utils';
import {DEFAULT_MAX_ZOOM, SVGViewport} from '../graph/SVGViewport';
import {useAssetLayout} from '../graph/asyncGraphLayout';
import {isNodeOffscreen} from '../graph/common';
import {AssetKeyInput} from '../graphql/types';
import {getJSONForKey} from '../hooks/useStateWithStorage';

const LINEAGE_GRAPH_ZOOM_LEVEL = 'lineageGraphZoomLevel';

export const AssetNodeLineageGraph = ({
  assetKey,
  assetGraphData,
  params,
  columnLineageData,
  column,
}: {
  assetKey: AssetKeyInput;
  assetGraphData: GraphData;
  params: AssetViewParams;
  columnLineageData: AssetColumnLineages;
  column: string | undefined;
}) => {
  const assetGraphId = toGraphId(assetKey);

  const {allGroups, groupedAssets} = useMemo(() => {
    const groupedAssets: Record<string, GraphNode[]> = {};
    Object.values(assetGraphData.nodes).forEach((node) => {
      const groupId = groupIdForNode(node);
      groupedAssets[groupId] = groupedAssets[groupId] || [];
      groupedAssets[groupId]!.push(node);
    });
    return {allGroups: Object.keys(groupedAssets), groupedAssets};
  }, [assetGraphData]);

  const [highlighted, setHighlighted] = useState<string[] | null>(null);

  const {layout, loading} = useAssetLayout(assetGraphData, allGroups, 'horizontal');
  const viewportEl = useRef<SVGViewport>();
  const history = useHistory();

  const onClickAsset = (key: AssetKey) => {
    history.push(assetDetailsPathForKey(key, {...params, lineageScope: 'neighbors'}));
  };

  useEffect(() => {
    if (viewportEl.current && layout) {
      const lastZoomLevel = Number(getJSONForKey(LINEAGE_GRAPH_ZOOM_LEVEL));
      viewportEl.current.autocenter(false, lastZoomLevel);
      viewportEl.current.focus();
    }
  }, [viewportEl, layout, assetGraphId]);

  if (!layout || loading) {
    return (
      <Box style={{flex: 1}} flex={{alignItems: 'center', justifyContent: 'center'}}>
        <Spinner purpose="page" />
      </Box>
    );
  }

  const visibleColumns: {[graphId: string]: AssetColumnLineageLocal[''][]} = {};
  const visibleEdges: typeof layout.edges = [];

  if (column) {
    type Item = {graphId: string; column: string};
    const visited = new Set<string>();
    const queue: Item[] = [{graphId: assetGraphId, column}];
    let item: Item | undefined;

    while ((item = queue.pop())) {
      if (!item) {
        continue;
      }
      const {graphId, column} = item;
      visited.add(JSON.stringify(item));

      let lineageForColumn = columnLineageData[graphId]?.[column];
      if (!lineageForColumn) {
        lineageForColumn = {
          name: column,
          description: 'Not found in column metadata',
          type: null,
          downstream: [],
          upstream: [],
        };
      }

      visibleColumns[graphId] = visibleColumns[graphId] || [];
      visibleColumns[graphId]?.push(lineageForColumn);

      for (const upstream of lineageForColumn.upstream) {
        for (const upstreamAssetKey of upstream.assetKeys) {
          const upstreamGraphId = toGraphId(upstreamAssetKey);
          const item = {graphId: upstreamGraphId, column: upstream.columnName};
          if (!visited.has(JSON.stringify(item))) {
            queue.push(item);
            const edge = layout.edges.find(
              (e) => e.fromId === upstreamGraphId && e.toId === graphId,
            );
            if (edge) {
              visibleEdges.push(edge);
            }
          }
        }
      }
      for (const downstream of lineageForColumn.downstream) {
        for (const downstreamAssetKey of downstream.assetKeys) {
          const downstreamGraphId = toGraphId(downstreamAssetKey);
          const item = {graphId: downstreamGraphId, column: downstream.columnName};
          if (!visited.has(JSON.stringify(item))) {
            queue.push(item);
            const edge = layout.edges.find(
              (e) => e.fromId === downstreamGraphId && e.toId === graphId,
            );
            if (edge) {
              visibleEdges.push(edge);
            }
          }
        }
      }
    }
  }

  return (
    <SVGViewport
      ref={(r) => (viewportEl.current = r || undefined)}
      interactor={SVGViewport.Interactors.PanAndZoom}
      defaultZoom="zoom-to-fit"
      graphWidth={layout.width}
      graphHeight={layout.height}
      onDoubleClick={(e) => {
        viewportEl.current?.autocenter(true);
        e.stopPropagation();
      }}
      maxZoom={DEFAULT_MAX_ZOOM}
      maxAutocenterZoom={DEFAULT_MAX_ZOOM}
    >
      {({scale}, viewportRect) => (
        <SVGContainer width={layout.width} height={layout.height}>
          {viewportEl.current && <SVGSaveZoomLevel scale={scale} />}

          {Object.values(layout.groups)
            .filter((node) => !isNodeOffscreen(node.bounds, viewportRect))
            .sort((a, b) => a.id.length - b.id.length)
            .map((group) => (
              <foreignObject
                {...group.bounds}
                key={`${group.id}-outline`}
                onDoubleClick={(e) => {
                  e.stopPropagation();
                }}
              >
                <GroupOutline $minimal={scale < MINIMAL_SCALE} />
              </foreignObject>
            ))}

          <AssetEdges
            selected={null}
            highlighted={highlighted}
            edges={column ? visibleEdges : layout.edges}
            viewportRect={viewportRect}
            direction="horizontal"
          />

          {Object.values(layout.groups)
            .filter((node) => !isNodeOffscreen(node.bounds, viewportRect))
            .sort((a, b) => a.id.length - b.id.length)
            .map((group) => (
              <foreignObject {...group.bounds} key={group.id}>
                <ExpandedGroupNode
                  group={{...group, assets: groupedAssets[group.id]!}}
                  minimal={scale < MINIMAL_SCALE}
                  setHighlighted={setHighlighted}
                />
              </foreignObject>
            ))}

          {Object.values(layout.nodes)
            .filter((node) => !isNodeOffscreen(node.bounds, viewportRect))
            .map(({id, bounds}) => {
              const graphNode = assetGraphData.nodes[id];
              const path = JSON.parse(id);

              const contextMenuProps = {
                graphData: assetGraphData,
                node: graphNode!,
              };

              return (
                <foreignObject
                  {...bounds}
                  key={id}
                  style={{overflow: 'visible'}}
                  onMouseEnter={() => setHighlighted([id])}
                  onMouseLeave={() => setHighlighted(null)}
                  onClick={() => onClickAsset({path})}
                  onDoubleClick={(e) => {
                    viewportEl.current?.zoomToSVGBox(bounds, true, 1.2);
                    e.stopPropagation();
                  }}
                >
                  {!graphNode ? (
                    <AssetNodeLink assetKey={{path}} />
                  ) : column ? (
                    <AssetColumnsNode
                      definition={graphNode.definition}
                      columns={visibleColumns[graphNode.id] || []}
                      selected={graphNode.id === assetGraphId}
                    />
                  ) : scale < MINIMAL_SCALE ? (
                    <AssetNodeContextMenuWrapper {...contextMenuProps}>
                      <AssetNodeMinimal
                        definition={graphNode.definition}
                        selected={graphNode.id === assetGraphId}
                        height={bounds.height}
                      />
                    </AssetNodeContextMenuWrapper>
                  ) : (
                    <AssetNodeContextMenuWrapper {...contextMenuProps}>
                      <AssetNode
                        definition={graphNode.definition}
                        selected={graphNode.id === assetGraphId}
                      />
                    </AssetNodeContextMenuWrapper>
                  )}
                </foreignObject>
              );
            })}
        </SVGContainer>
      )}
    </SVGViewport>
  );
};

const SVGSaveZoomLevel = ({scale}: {scale: number}) => {
  useEffect(() => {
    try {
      window.localStorage.setItem(LINEAGE_GRAPH_ZOOM_LEVEL, JSON.stringify(scale));
    } catch (err) {
      // no-op
    }
  }, [scale]);
  return <></>;
};

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
`;
