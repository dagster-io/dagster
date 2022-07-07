import {Page, PageHeader, Heading} from '@dagster-io/ui';
import * as React from 'react';
import {useHistory, useParams} from 'react-router-dom';

import {AssetGraphExplorer} from '../asset-graph/AssetGraphExplorer';
import {AssetGraphFetchScope} from '../asset-graph/useAssetGraphData';
import {AssetLocation} from '../asset-graph/useFindAssetLocation';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {RepoFilterButton} from '../instance/RepoFilterButton';
import {
  ExplorerPath,
  explorerPathFromString,
  explorerPathToString,
} from '../pipelines/PipelinePathUtils';
import {ReloadAllButton} from '../workspace/ReloadAllButton';
import {WorkspaceContext} from '../workspace/WorkspaceContext';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';

interface AssetGroupRootParams {
  0: string;
}

const __GLOBAL__ = '__GLOBAL__';

export const AssetsGroupsGlobalGraphRoot: React.FC = () => {
  const {0: path} = useParams<AssetGroupRootParams>();
  const {allRepos, visibleRepos} = React.useContext(WorkspaceContext);
  const history = useHistory();

  useDocumentTitle(`Global Asset Lineage`);

  const onChangeExplorerPath = React.useCallback(
    (path: ExplorerPath, mode: 'push' | 'replace') => {
      history[mode](
        `/instance/asset-groups${explorerPathToString({...path, pipelineName: __GLOBAL__}).replace(
          __GLOBAL__,
          '',
        )}`,
      );
    },
    [history],
  );

  const onNavigateToForeignNode = React.useCallback(
    (node: AssetLocation) => {
      history.push(assetDetailsPathForKey(node.assetKey, {view: 'definition'}));
    },
    [history],
  );

  const fetchOptions = React.useMemo(() => {
    const options: AssetGraphFetchScope = {
      hideEdgesToNodesOutsideQuery: false,
      hideNodesMatching: (node) => {
        return !visibleRepos.some(
          (repo) =>
            repo.repositoryLocation.name === node.repository.location.name &&
            repo.repository.name === node.repository.name,
        );
      },
    };
    return options;
  }, [visibleRepos]);

  return (
    <Page style={{display: 'flex', flexDirection: 'column', paddingBottom: 0}}>
      <PageHeader
        title={<Heading>Global Asset Lineage</Heading>}
        right={
          <div style={{marginBottom: -8}}>
            <ReloadAllButton label="Reload definitions" />
          </div>
        }
      />
      <AssetGraphExplorer
        fetchOptions={fetchOptions}
        fetchOptionFilters={<>{allRepos.length > 1 && <RepoFilterButton />}</>}
        options={{preferAssetRendering: true, explodeComposites: true}}
        explorerPath={explorerPathFromString(__GLOBAL__ + path || '/')}
        onChangeExplorerPath={onChangeExplorerPath}
        onNavigateToForeignNode={onNavigateToForeignNode}
      />
    </Page>
  );
};
