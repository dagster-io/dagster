import {Colors, Spinner} from '@dagster-io/ui';
import React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import {withMiddleTruncation} from '../app/Util';
import {AssetConnectedEdges} from '../asset-graph/AssetEdges';
import {AssetNodeMinimal, NameMinimal, AssetNode} from '../asset-graph/AssetNode';
import {ForeignNode} from '../asset-graph/ForeignNode';
import {
  buildComputeStatusData,
  displayNameForAssetKey,
  GraphData,
  LiveData,
  toGraphId,
} from '../asset-graph/Utils';
import {SVGViewport} from '../graph/SVGViewport';
import {useAssetLayout} from '../graph/asyncGraphLayout';

import {AssetKey} from './types';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinitionFragment';

const EXPERIMENTAL_MINI_SCALE = 0.5;

export const AssetNodeLineageGraph: React.FC<{
  assetNode: AssetNodeDefinitionFragment;
  assetGraphData: GraphData;
  liveDataByNode: LiveData;
}> = ({assetNode, assetGraphData, liveDataByNode}) => {
  const assetGraphId = toGraphId(assetNode.assetKey);

  const [highlighted, setHighlighted] = React.useState<string | null>(null);
  console.log(assetGraphData);
  const {layout, loading} = useAssetLayout(assetGraphData);
  const viewportEl = React.useRef<SVGViewport>();
  const history = useHistory();

  const onClickAsset = (key: AssetKey) => {
    history.replace(`/instance/assets/${key.path.join('/')}?view=lineage`);
  };

  React.useEffect(() => {
    if (viewportEl.current && layout) {
      viewportEl.current.zoomToSVGBox(layout.nodes[assetGraphId].bounds, false, 1.1);
      viewportEl.current.focus();
    }
  }, [viewportEl, layout, assetGraphId]);

  const computeStatuses = React.useMemo(
    () => buildComputeStatusData(assetGraphData, liveDataByNode),
    [assetGraphData, liveDataByNode],
  );

  if (!layout || loading) {
    return <Spinner purpose="page" />;
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
      {({scale: _scale}) => (
        <SVGContainer width={layout.width} height={layout.height}>
          <AssetConnectedEdges highlighted={highlighted} edges={layout.edges} />

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
                ) : _scale < EXPERIMENTAL_MINI_SCALE ? (
                  <AssetNodeMinimal
                    style={{background: Colors.White}}
                    selected={graphNode.id === assetGraphId}
                  >
                    <NameMinimal style={{fontSize: 28}}>
                      {withMiddleTruncation(displayNameForAssetKey(graphNode.definition.assetKey), {
                        maxLength: 17,
                      })}
                    </NameMinimal>
                  </AssetNodeMinimal>
                ) : (
                  <AssetNode
                    definition={graphNode.definition}
                    liveData={liveDataByNode[graphNode.id]}
                    computeStatus={computeStatuses[graphNode.id]}
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

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
`;
