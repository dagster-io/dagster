import {Spinner} from '@dagster-io/ui';
import React from 'react';
import {useHistory} from 'react-router-dom';

import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {AssetGraphExplorerWithData} from '../asset-graph/AssetGraphExplorer';
import {LiveData, tokenForAssetKey} from '../asset-graph/Utils';
import {useAssetGraphData} from '../asset-graph/useAssetGraphData';
import {useLiveDataForAssetKeys} from '../asset-graph/useLiveDataForAssetKeys';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useDidLaunchEvent} from '../runs/RunUtils';

import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinitionFragment';

export const AssetNodeLineageGraph: React.FC<{
  assetNode: AssetNodeDefinitionFragment;
  liveDataByNode: LiveData;
}> = ({assetNode}) => {
  const {
    assetGraphData,
    graphQueryItems,
    graphAssetKeys,
    allAssetKeys,
    applyingEmptyDefault,
  } = useAssetGraphData(null, `+"${tokenForAssetKey(assetNode.assetKey)}"+`);

  const history = useHistory();
  const {liveResult, liveDataByNode} = useLiveDataForAssetKeys(
    assetGraphData?.nodes,
    graphAssetKeys,
  );
  const liveDataRefreshState = useQueryRefreshAtInterval(liveResult, FIFTEEN_SECONDS);

  useDocumentTitle('Assets');
  useDidLaunchEvent(liveResult.refetch);

  if (!assetGraphData || !allAssetKeys) {
    return <Spinner purpose="page" />;
  }
  return (
    <AssetGraphExplorerWithData
      key={assetNode.id}
      assetGraphData={assetGraphData}
      allAssetKeys={allAssetKeys}
      graphQueryItems={graphQueryItems}
      applyingEmptyDefault={applyingEmptyDefault}
      liveDataRefreshState={liveDataRefreshState}
      liveDataByNode={liveDataByNode}
      options={{preferAssetRendering: true, explodeComposites: false, enableSidebar: false}}
      explorerPath={{
        opNames: [tokenForAssetKey(assetNode.assetKey)],
        opsQuery: '',
        pipelineName: '',
        explodeComposites: false,
      }}
      onChangeExplorerPath={(path) => {
        const [op] = path.opNames;
        if (op) {
          history.replace(`/instance/assets/${op}?view=lineage`);
        }
      }}
    />
  );
};
