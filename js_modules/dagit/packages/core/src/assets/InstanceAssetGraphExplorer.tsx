import {Box, Colors, Heading, PageHeader} from '@dagster-io/ui';
import * as React from 'react';
import {useParams} from 'react-router';
import {useHistory} from 'react-router-dom';

import {AssetGraphExplorer} from '../asset-graph/AssetGraphExplorer';
import {AssetGraphQuery_assetNodes} from '../asset-graph/types/AssetGraphQuery';
import {RepoFilterButton} from '../instance/RepoFilterButton';
import {
  instanceAssetsExplorerPathFromString,
  instanceAssetsExplorerPathToURL,
} from '../pipelines/PipelinePathUtils';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoPath} from '../workspace/buildRepoAddress';

import {AssetViewModeSwitch} from './AssetViewModeSwitch';
import {useAssetView} from './useAssetView';

export const InstanceAssetGraphExplorer: React.FC = () => {
  const params = useParams();
  const history = useHistory();
  const [_, _setView] = useAssetView();
  const {visibleRepos} = React.useContext(WorkspaceContext);
  const explorerPath = instanceAssetsExplorerPathFromString(params[0]);

  const filterNodes = React.useMemo(() => {
    const visibleRepoAddresses = visibleRepos.map((v) =>
      buildRepoPath(v.repository.name, v.repositoryLocation.name),
    );
    return (node: AssetGraphQuery_assetNodes) =>
      visibleRepoAddresses.includes(
        buildRepoPath(node.repository.name, node.repository.location.name),
      );
  }, [visibleRepos]);

  return (
    <Box
      flex={{direction: 'column', justifyContent: 'stretch'}}
      style={{height: '100%', position: 'relative'}}
    >
      <PageHeader title={<Heading>Assets</Heading>} />
      <Box
        background={Colors.White}
        padding={{horizontal: 24, vertical: 8}}
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
        <RepoFilterButton />
      </Box>
      <AssetGraphExplorer
        options={{preferAssetRendering: true, explodeComposites: true}}
        filterNodes={filterNodes}
        explorerPath={explorerPath}
        onChangeExplorerPath={(path, mode) => {
          history[mode](instanceAssetsExplorerPathToURL(path));
        }}
      />
    </Box>
  );
};
