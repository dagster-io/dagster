import {Box, Button, ButtonGroup, Checkbox, Colors, Icon} from '@dagster-io/ui';
import * as React from 'react';

import {GraphData, LiveData} from '../asset-graph/Utils';

import {AssetLineageScope, AssetNodeLineageGraph} from './AssetNodeLineageGraph';
import {AssetViewParams} from './AssetView';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinitionFragment';

export const AssetNodeLineage: React.FC<{
  params: AssetViewParams;
  setParams: (params: AssetViewParams) => void;
  assetNode: AssetNodeDefinitionFragment;
  assetGraphData: GraphData;
  liveDataByNode: LiveData;
}> = ({params, setParams, assetNode, liveDataByNode, assetGraphData}) => {
  return (
    <>
      <Box
        flex={{justifyContent: 'space-between', alignItems: 'center', gap: 12}}
        padding={{left: 24, right: 12, vertical: 12}}
        border={{side: 'bottom', color: Colors.KeylineGray, width: 1}}
      >
        <ButtonGroup<AssetLineageScope>
          activeItems={new Set([params.lineageScope || 'neighbors'])}
          buttons={[
            {id: 'neighbors', label: 'Nearest Neighbors', icon: 'graph_neighbors'},
            {id: 'upstream', label: 'Upstream', icon: 'graph_upstream'},
            {id: 'downstream', label: 'Downstream', icon: 'graph_downstream'},
          ]}
          onClick={(lineageScope) => setParams({...params, lineageScope})}
        />
        <Checkbox
          format="switch"
          label="Show secondary edges"
          checked={!!params.lineageShowSecondaryEdges}
          onChange={() =>
            setParams({
              ...params,
              lineageShowSecondaryEdges: params.lineageShowSecondaryEdges ? undefined : true,
            })
          }
        />
        <div style={{flex: 1}} />
        {Object.values(assetGraphData.nodes).length > 1 ? (
          <LaunchAssetExecutionButton
            assetKeys={Object.values(assetGraphData.nodes).map((n) => n.assetKey)}
            liveDataByNode={liveDataByNode}
            intent="none"
            context="all"
          />
        ) : (
          <Button icon={<Icon name="materialization" />} disabled>
            Materialize all
          </Button>
        )}
      </Box>
      <AssetNodeLineageGraph
        assetNode={assetNode}
        liveDataByNode={liveDataByNode}
        assetGraphData={assetGraphData}
        params={params}
      />
    </>
  );
};
