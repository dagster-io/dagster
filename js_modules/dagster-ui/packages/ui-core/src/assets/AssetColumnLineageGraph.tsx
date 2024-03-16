import {Box, Spinner} from '@dagster-io/ui-components';
import {useRef, useState} from 'react';
import styled from 'styled-components';

import {SVGSaveZoomLevel, useLastSavedZoomLevel} from './SavedZoomLevel';
import {AssetColumnLineages} from './lineage/useColumnLineageDataForAssets';
import {fromColumnGraphId, useColumnLineageLayout} from './useColumnLineageLayout';
import {AssetColumnNode, AssetColumnsGroupNode} from '../asset-graph/AssetColumnsNode';
import {AssetEdges} from '../asset-graph/AssetEdges';
import {AssetNodeContextMenuWrapper} from '../asset-graph/AssetNode';
import {AssetNodeLink} from '../asset-graph/ForeignNode';
import {GraphData, fromGraphId, toGraphId} from '../asset-graph/Utils';
import {DEFAULT_MAX_ZOOM, SVGViewport} from '../graph/SVGViewport';
import {isNodeOffscreen} from '../graph/common';
import {AssetKeyInput} from '../graphql/types';

export const AssetColumnLineageGraph = ({
  assetKey,
  assetGraphData,
  columnLineageData,
  column,
}: {
  assetKey: AssetKeyInput;
  assetGraphData: GraphData;
  columnLineageData: AssetColumnLineages;
  column: string;
}) => {
  const assetGraphId = toGraphId(assetKey);

  const [highlighted, setHighlighted] = useState<string[] | null>(null);

  const {layout, loading} = useColumnLineageLayout(
    assetGraphData,
    assetGraphId,
    column,
    columnLineageData,
  );

  const viewportEl = useRef<SVGViewport>();
  //   const history = useHistory();

  //   const onClickAsset = (key: AssetKey) => {
  //     history.push(assetDetailsPathForKey(key, {...params, lineageScope: 'neighbors'}));
  //   };

  useLastSavedZoomLevel(viewportEl, layout, assetGraphId);

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

              return (
                <foreignObject
                  {...bounds}
                  key={id}
                  style={{overflow: 'visible'}}
                  onMouseEnter={() => setHighlighted([id])}
                  onMouseLeave={() => setHighlighted(null)}
                  // onClick={() => onClickAsset({path})}
                  onDoubleClick={(e) => {
                    viewportEl.current?.zoomToSVGBox(bounds, true, 1.2);
                    e.stopPropagation();
                  }}
                >
                  <AssetNodeContextMenuWrapper {...contextMenuProps}>
                    <AssetColumnsGroupNode
                      definition={graphNode!.definition}
                      selected={assetGraphId === groupAssetGraphId}
                      height={bounds.height}
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
              const graphNode = assetGraphData.nodes[assetGraphId];

              const col = columnLineageData[assetGraphId]?.[column] || {
                name: column,
                description: 'Not found in column metadata',
                type: null,
                upstream: [],
              };

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
                  onDoubleClick={(e) => {
                    viewportEl.current?.zoomToSVGBox(bounds, true, 1.2);
                    e.stopPropagation();
                  }}
                >
                  {!graphNode ? (
                    <AssetNodeLink assetKey={assetKey} />
                  ) : (
                    <AssetNodeContextMenuWrapper {...contextMenuProps}>
                      <AssetColumnNode column={col} />
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

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
`;
