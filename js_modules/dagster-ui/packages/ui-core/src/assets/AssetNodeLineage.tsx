import {Box, Button, ButtonGroup, Colors, Icon} from '@dagster-io/ui-components';
import React, {useContext, useMemo} from 'react';
import styled from 'styled-components';

import {AssetFeatureContext} from './AssetFeatureContext';
import {AssetNodeLineageGraph} from './AssetNodeLineageGraph';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {LineageDepthControl} from './LineageDepthControl';
import {AssetLineageScope, AssetViewParams} from './types';
import {GraphData} from '../asset-graph/Utils';
import {AssetGraphQueryItem, calculateGraphDistances} from '../asset-graph/useAssetGraphData';
import {AssetKeyInput} from '../graphql/types';

export const AssetNodeLineage = ({
  params,
  setParams,
  assetKey,
  assetGraphData,
  graphQueryItems,
  requestedDepth,
}: {
  params: AssetViewParams;
  setParams: (params: AssetViewParams) => void;
  assetKey: AssetKeyInput;
  assetGraphData: GraphData;
  requestedDepth: number;
  graphQueryItems: AssetGraphQueryItem[];
}) => {
  // Note: Default needs to be here and not in the context declaration to avoid circular imports
  const {LineageOptions, LineageGraph = AssetNodeLineageGraph} = useContext(AssetFeatureContext);

  const maxDistances = useMemo(
    () => calculateGraphDistances(graphQueryItems, assetKey),
    [graphQueryItems, assetKey],
  );
  const maxDepth =
    params.lineageScope === 'upstream'
      ? maxDistances.upstream
      : params.lineageScope === 'downstream'
      ? maxDistances.downstream
      : Math.max(maxDistances.upstream, maxDistances.downstream);

  const currentDepth = Math.max(1, Math.min(maxDepth, requestedDepth));

  return (
    <Box
      style={{width: '100%', flex: 1, minHeight: 0, position: 'relative'}}
      flex={{direction: 'column'}}
    >
      <Box
        flex={{justifyContent: 'space-between', alignItems: 'center', gap: 12}}
        padding={{left: 24, right: 12, vertical: 12}}
        border="bottom"
      >
        <ButtonGroup<AssetLineageScope>
          activeItems={new Set([params.lineageScope || 'neighbors'])}
          buttons={[
            {id: 'neighbors', label: 'Nearest Neighbors', icon: 'graph_neighbors'},
            {id: 'upstream', label: 'Upstream', icon: 'graph_upstream'},
            {id: 'downstream', label: 'Downstream', icon: 'graph_downstream'},
          ]}
          onClick={(lineageScope) => setParams({...params, lineageScope, lineageDepth: undefined})}
        />
        <LineageDepthControl
          value={currentDepth}
          onChange={(depth) => setParams({...params, lineageDepth: depth})}
          max={maxDepth}
        />

        {LineageOptions && (
          <LineageOptions assetKey={assetKey} params={params} setParams={setParams} />
        )}

        <div style={{flex: 1}} />
        {Object.values(assetGraphData.nodes).length > 1 ? (
          <LaunchAssetExecutionButton
            primary={false}
            scope={{all: Object.values(assetGraphData.nodes).map((n) => n.definition)}}
          />
        ) : (
          <Button icon={<Icon name="materialization" />} disabled>
            Materialize all
          </Button>
        )}
      </Box>
      {currentDepth < maxDepth && (
        <DepthHidesAssetsNotice>
          Not all upstream/downstream assets shown. Increase the depth to show more.
        </DepthHidesAssetsNotice>
      )}
      <LineageGraph params={params} assetKey={assetKey} assetGraphData={assetGraphData} />
    </Box>
  );
};

const DepthHidesAssetsNotice = styled.div`
  background: ${Colors.backgroundLight()};
  border-radius: 8px;
  color: ${Colors.textLight()};
  align-items: center;
  display: flex;
  padding: 4px 8px;
  gap: 4px;
  position: absolute;
  right: 12px;
  top: 70px;
  z-index: 2;
`;
