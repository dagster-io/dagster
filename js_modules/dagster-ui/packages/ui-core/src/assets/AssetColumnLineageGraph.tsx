import {Box, Spinner} from '@dagster-io/ui-components';
import {useRef, useState} from 'react';
import styled from 'styled-components';

import {SVGSaveZoomLevel, useLastSavedZoomLevel} from './SavedZoomLevel';
import {AssetColumnLineages} from './lineage/useColumnLineageDataForAssets';
import {fromColumnGraphId, useColumnLineageLayout} from './useColumnLineageLayout';
import {AssetColumnNode, AssetColumnsGroupNode} from '../asset-graph/AssetColumnsNode';
import {AssetEdges} from '../asset-graph/AssetEdges';
import {AssetNodeContextMenuWrapper} from '../asset-graph/AssetNode';
import {GraphData, fromGraphId, toGraphId} from '../asset-graph/Utils';
import {DEFAULT_MAX_ZOOM, SVGViewport} from '../graph/SVGViewport';
import {isNodeOffscreen} from '../graph/common';
import {AssetKeyInput} from '../graphql/types';

export const AssetColumnLineageGraph = ({
  assetKey,
  assetGraphData,
  columnLineageData,
  focusedColumn,
}: {
  assetKey: AssetKeyInput;
  assetGraphData: GraphData;
  columnLineageData: AssetColumnLineages;
  focusedColumn: string;
}) => {
  const focusedAssetGraphId = toGraphId(assetKey);

  const [highlighted, setHighlighted] = useState<string[] | null>(null);

  const {layout, loading} = useColumnLineageLayout(
    assetGraphData,
    focusedAssetGraphId,
    focusedColumn,
    columnLineageData,
  );

  const viewportEl = useRef<SVGViewport>();

  useLastSavedZoomLevel(viewportEl, layout, focusedAssetGraphId);

  if (!layout || loading) {
    return (
      <Box style={{flex: 1}} flex={{alignItems: 'center', justifyContent: 'center'}}>
        <Spinner purpose="page" />
      </Box>
    );
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
            .map(({id, bounds}) => {
              const groupAssetGraphId = toGraphId({path: id.split(':').pop()!.split('>')});
              const graphNode = assetGraphData.nodes[groupAssetGraphId];
              const contextMenuProps = {
                graphData: assetGraphData,
                node: graphNode!,
              };

              const cols = columnLineageData[groupAssetGraphId] || {};
              const colsAsOf = Object.values(cols)[0]?.asOf;

              return (
                <foreignObject
                  {...bounds}
                  key={id}
                  style={{overflow: 'visible'}}
                  onMouseEnter={() => setHighlighted([id])}
                  onMouseLeave={() => setHighlighted(null)}
                  onDoubleClick={(e) => {
                    viewportEl.current?.zoomToSVGBox(bounds, true, 1.2);
                    e.stopPropagation();
                  }}
                >
                  <AssetNodeContextMenuWrapper {...contextMenuProps}>
                    <AssetColumnsGroupNode
                      definition={graphNode!.definition}
                      selected={focusedAssetGraphId === groupAssetGraphId}
                      height={bounds.height}
                      asOf={colsAsOf}
                    />
                  </AssetNodeContextMenuWrapper>
                </foreignObject>
              );
            })}

          <AssetEdges
            selected={null}
            highlighted={highlighted}
            edges={layout.edges}
            viewportRect={viewportRect}
            direction="horizontal"
          />

          {Object.values(layout.nodes)
            .filter((node) => !isNodeOffscreen(node.bounds, viewportRect))
            .map(({id, bounds}) => {
              const {assetGraphId, column} = fromColumnGraphId(id);
              const assetKey = fromGraphId(assetGraphId);

              const col = columnLineageData[assetGraphId]?.[column] || {
                name: column,
                description: 'Not found in column metadata',
                type: null,
                upstream: [],
                asOf: undefined,
              };

              return (
                <foreignObject
                  {...bounds}
                  key={id}
                  style={{overflow: 'visible'}}
                  onMouseEnter={() => setHighlighted([id])}
                  onMouseLeave={() => setHighlighted(null)}
                  onDoubleClick={(e) => {
                    viewportEl.current?.zoomToSVGBox(bounds, true, 1.2);
                    e.stopPropagation();
                  }}
                >
                  <AssetColumnNode
                    assetKey={assetKey}
                    column={col}
                    selected={assetGraphId === focusedAssetGraphId && focusedColumn === column}
                  />
                </foreignObject>
              );
            })}
        </SVGContainer>
      )}
    </SVGViewport>
  );
};

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
`;
