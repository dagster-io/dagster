import {Box, Spinner} from '@dagster-io/ui';
import React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import {AssetConnectedEdges} from '../asset-graph/AssetEdges';
import {MINIMAL_SCALE} from '../asset-graph/AssetGraphExplorer';
import {AssetGroupNode} from '../asset-graph/AssetGroupNode';
import {AssetNodeMinimal, AssetNode} from '../asset-graph/AssetNode';
import {ForeignNode} from '../asset-graph/ForeignNode';
import {GraphData, LiveData, toGraphId} from '../asset-graph/Utils';
import {SVGViewport} from '../graph/SVGViewport';
import {useAssetLayout} from '../graph/asyncGraphLayout';
import {getJSONForKey} from '../hooks/useStateWithStorage';

import {AssetViewParams} from './AssetView';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetKey} from './types';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinitionFragment';

const LINEAGE_GRAPH_ZOOM_LEVEL = 'lineageGraphZoomLevel';

export type AssetLineageScope = 'neighbors' | 'upstream' | 'downstream';

export const AssetNodeLineageGraph: React.FC<{
  assetNode: AssetNodeDefinitionFragment;
  assetGraphData: GraphData;
  liveDataByNode: LiveData;
  params: AssetViewParams;
}> = ({assetNode, assetGraphData, liveDataByNode, params}) => {
  const assetGraphId = toGraphId(assetNode.assetKey);

  const [highlighted, setHighlighted] = React.useState<string | null>(null);

  const {layout, loading} = useAssetLayout(assetGraphData);
  const viewportEl = React.useRef<SVGViewport>();
  const history = useHistory();

  const onClickAsset = (key: AssetKey) => {
    history.push(assetDetailsPathForKey(key, {...params, lineageScope: 'neighbors'}));
  };

  React.useEffect(() => {
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

  return (
    <SVGViewport
      ref={(r) => (viewportEl.current = r || undefined)}
      interactor={SVGViewport.Interactors.PanAndZoom}
      graphWidth={layout.width}
      graphHeight={layout.height}
      onDoubleClick={(e) => {
        viewportEl.current?.autocenter(true);
        e.stopPropagation();
      }}
      maxZoom={1.2}
      maxAutocenterZoom={1.2}
    >
      {({scale}) => (
        <SVGContainer width={layout.width} height={layout.height}>
          {viewportEl.current && <SVGSaveZoomLevel scale={scale} />}
          <AssetConnectedEdges highlighted={highlighted} edges={layout.edges} />

          {Object.values(layout.groups)
            .sort((a, b) => a.id.length - b.id.length)
            .map((group) => (
              <foreignObject {...group.bounds} key={group.id}>
                <AssetGroupNode group={group} scale={scale} />
              </foreignObject>
            ))}

          {Object.values(layout.nodes).map(({id, bounds}) => {
            const graphNode = assetGraphData.nodes[id];
            const path = JSON.parse(id);

            return (
              <foreignObject
                {...bounds}
                key={id}
                style={{overflow: 'visible'}}
                onMouseEnter={() => setHighlighted(id)}
                onMouseLeave={() => setHighlighted(null)}
                onClick={() => onClickAsset({path})}
                onDoubleClick={(e) => {
                  viewportEl.current?.zoomToSVGBox(bounds, true, 1.2);
                  e.stopPropagation();
                }}
              >
                {!graphNode || !graphNode.definition.opNames.length ? (
                  <ForeignNode assetKey={{path}} />
                ) : scale < MINIMAL_SCALE ? (
                  <AssetNodeMinimal
                    definition={graphNode.definition}
                    selected={graphNode.id === assetGraphId}
                  />
                ) : (
                  <AssetNode
                    definition={graphNode.definition}
                    liveData={liveDataByNode[graphNode.id]}
                    selected={graphNode.id === assetGraphId}
                  />
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
  React.useEffect(() => {
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
