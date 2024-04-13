import {Box, Spinner} from '@dagster-io/ui-components';
import {useMemo, useRef, useState} from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components';

import {SVGSaveZoomLevel, useLastSavedZoomLevel} from './SavedZoomLevel';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetKey, AssetViewParams} from './types';
import {AssetEdges} from '../asset-graph/AssetEdges';
import {MINIMAL_SCALE} from '../asset-graph/AssetGraphExplorer';
import {AssetNode, AssetNodeContextMenuWrapper, AssetNodeMinimal} from '../asset-graph/AssetNode';
import {ExpandedGroupNode, GroupOutline} from '../asset-graph/ExpandedGroupNode';
import {AssetNodeLink} from '../asset-graph/ForeignNode';
import {GraphData, GraphNode, groupIdForNode, toGraphId} from '../asset-graph/Utils';
import {LayoutAssetGraphOptions} from '../asset-graph/layout';
import {DEFAULT_MAX_ZOOM, SVGViewport} from '../graph/SVGViewport';
import {useAssetLayout} from '../graph/asyncGraphLayout';
import {isNodeOffscreen} from '../graph/common';
import {AssetKeyInput} from '../graphql/types';

const LINEAGE_GRAPH_OPTIONS: LayoutAssetGraphOptions = {direction: 'horizontal'};

export type AssetNodeLineageGraphProps = {
  assetKey: AssetKeyInput;
  assetGraphData: GraphData;
  params: AssetViewParams;
};

export const AssetNodeLineageGraph = ({
  assetKey,
  assetGraphData,
  params,
}: AssetNodeLineageGraphProps) => {
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

  const {layout, loading} = useAssetLayout(assetGraphData, allGroups, LINEAGE_GRAPH_OPTIONS);
  const viewportEl = useRef<SVGViewport>();
  const history = useHistory();

  const onClickAsset = (key: AssetKey) => {
    history.push(assetDetailsPathForKey(key, {...params, lineageScope: 'neighbors'}));
  };

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
            edges={layout.edges}
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

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
`;
