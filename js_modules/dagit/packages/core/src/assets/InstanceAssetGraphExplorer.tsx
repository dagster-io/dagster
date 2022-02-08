import {Body, Box, ColorsWIP, Heading, PageHeader} from '@dagster-io/ui';
import * as React from 'react';
import {useParams} from 'react-router';
import {useHistory} from 'react-router-dom';

import {RepoFilterButton} from '../instance/RepoFilterButton';
import {
  instanceAssetsExplorerPathFromString,
  instanceAssetsExplorerPathToURL,
} from '../pipelines/PipelinePathUtils';
import {AssetGraphExplorer} from '../workspace/asset-graph/AssetGraphExplorer';

import {AssetViewModeSwitch} from './AssetViewModeSwitch';
import {useAssetView} from './useAssetView';

export const InstanceAssetGraphExplorer: React.FC = () => {
  const params = useParams();
  const history = useHistory();
  const [_, _setView] = useAssetView();

  // This is a bit of a hack, but our explorer path needs a job name and we'd like
  // to continue sharing the parsing/stringifying logic from the job graph UI
  const explorerPath = instanceAssetsExplorerPathFromString(params[0]);

  return (
    <Box
      flex={{direction: 'column', justifyContent: 'stretch'}}
      style={{height: '100%', position: 'relative'}}
    >
      <PageHeader
        title={<Heading>Assets</Heading>}
        right={
          <Body color={ColorsWIP.Gray400} style={{marginTop: 4, marginRight: 12}}>
            Note: Graph view only displays software defined assets currently loaded in your
            workspace
          </Body>
        }
      />
      <Box
        background={ColorsWIP.White}
        padding={{horizontal: 24, vertical: 8}}
        border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
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
        <RepoFilterButton />
      </Box>
      <AssetGraphExplorer
        explorerPath={explorerPath}
        onChangeExplorerPath={(path, mode) => {
          history[mode](instanceAssetsExplorerPathToURL(path));
        }}
      />
    </Box>
  );
};
