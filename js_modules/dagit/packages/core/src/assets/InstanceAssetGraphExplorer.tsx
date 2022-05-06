import {Box, Colors, Heading, PageHeader} from '@dagster-io/ui';
import * as React from 'react';
import {useParams} from 'react-router';
import {useHistory} from 'react-router-dom';

import {AssetGraphExplorer} from '../asset-graph/AssetGraphExplorer';
import {
  instanceAssetsExplorerPathFromString,
  instanceAssetsExplorerPathToURL,
} from '../pipelines/PipelinePathUtils';
import {ReloadAllButton} from '../workspace/ReloadAllButton';

import {AssetViewModeSwitch} from './AssetViewModeSwitch';
import {useAssetView} from './useAssetView';

export const InstanceAssetGraphExplorer: React.FC = () => {
  const params = useParams();
  const history = useHistory();
  const [_, _setView] = useAssetView();
  const explorerPath = instanceAssetsExplorerPathFromString(params[0]);

  return (
    <Box
      flex={{direction: 'column', justifyContent: 'stretch'}}
      style={{height: '100%', position: 'relative'}}
    >
      <PageHeader title={<Heading>Assets</Heading>} />
      <Box
        background={Colors.White}
        padding={{left: 24, right: 12, vertical: 8}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        flex={{direction: 'row', gap: 12}}
      >
        <AssetViewModeSwitch
          view="graph"
          setView={(view) => {
            if (view !== 'graph') {
              _setView(view);
              history.push('/instance/assets');
            }
          }}
        />
        <div style={{flex: 1}} />
        <ReloadAllButton label="Reload definitions" />
      </Box>
      <AssetGraphExplorer
        options={{preferAssetRendering: true, explodeComposites: true}}
        explorerPath={explorerPath}
        onChangeExplorerPath={(path, mode) => {
          history[mode](instanceAssetsExplorerPathToURL(path));
        }}
      />
    </Box>
  );
};
