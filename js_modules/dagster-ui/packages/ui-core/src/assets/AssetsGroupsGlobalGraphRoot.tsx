import {Page, PageHeader, Heading} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import * as React from 'react';
import {useHistory, useParams} from 'react-router-dom';

import {AssetGraphExplorer} from '../asset-graph/AssetGraphExplorer';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetGraphFetchScope} from '../asset-graph/useAssetGraphData';
import {AssetLocation} from '../asset-graph/useFindAssetLocation';
import {AssetGroupSelector, AssetKeyInput} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {RepoFilterButton} from '../instance/RepoFilterButton';
import {
  ExplorerPath,
  explorerPathFromString,
  explorerPathToString,
} from '../pipelines/PipelinePathUtils';
import {ReloadAllButton} from '../workspace/ReloadAllButton';
import {WorkspaceContext} from '../workspace/WorkspaceContext';

import {AssetGroupSuggest, buildAssetGroupSelector} from './AssetGroupSuggest';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';

interface AssetGroupRootParams {
  0: string;
}

const __GLOBAL__ = '__GLOBAL__';

export function globalAssetGraphPathFor(path: Omit<ExplorerPath, 'pipelineName'>) {
  const str = explorerPathToString({...path, pipelineName: __GLOBAL__}).replace(__GLOBAL__, '');
  return `/asset-groups${str}`;
}

export function globalAssetGraphPathForAssetsAndDescendants(assetKeys: AssetKeyInput[]) {
  // Note: the max-length of a URL in chrome is 32k characters, and Firefox is 64k characters.
  // In a perfect world we populate ops query to "asset1*,asset2*" and then select the roots
  // by passing opNames. If we don't have enough characters to do both, just populate the ops
  // query. It might still be too long, but we tried.
  const opsQuery = assetKeys.map((a) => `${tokenForAssetKey(a)}*`).join(', ');
  const opNames = opsQuery.length > 16000 ? [] : [assetKeys.map(tokenForAssetKey).join(',')];
  return globalAssetGraphPathFor({opNames, opsQuery});
}

export const AssetsGroupsGlobalGraphRoot: React.FC = () => {
  const {0: path} = useParams<AssetGroupRootParams>();
  const {allRepos, visibleRepos} = React.useContext(WorkspaceContext);
  const history = useHistory();

  const [filters, setFilters] = useQueryPersistedState<{groups: AssetGroupSelector[]}>({
    encode: ({groups}) => ({groups: JSON.stringify(groups)}),
    decode: (qs) => ({groups: qs.groups ? JSON.parse(qs.groups) : []}),
  });

  useDocumentTitle(`Global Asset Lineage`);

  const onChangeExplorerPath = React.useCallback(
    (path: ExplorerPath, mode: 'push' | 'replace') => {
      history[mode]({
        pathname: globalAssetGraphPathFor(path),
        search: history.location.search,
      });
    },
    [history],
  );

  const onNavigateToSourceAssetNode = React.useCallback(
    (node: AssetLocation) => {
      history.push(assetDetailsPathForKey(node.assetKey, {view: 'definition'}));
    },
    [history],
  );

  const fetchOptions = React.useMemo(() => {
    const options: AssetGraphFetchScope = {
      hideEdgesToNodesOutsideQuery: false,
      hideNodesMatching: (node) => {
        if (
          !visibleRepos.some(
            (repo) =>
              repo.repositoryLocation.name === node.repository.location.name &&
              repo.repository.name === node.repository.name,
          )
        ) {
          return true;
        }
        if (filters.groups?.length) {
          const nodeGroup = buildAssetGroupSelector({definition: node});
          if (!filters.groups.some((g) => isEqual(g, nodeGroup))) {
            return true;
          }
        }

        return false;
      },
    };
    return options;
  }, [filters.groups, visibleRepos]);

  const assetGroups: AssetGroupSelector[] = React.useMemo(() => {
    return visibleRepos.flatMap((repo) =>
      repo.repository.assetGroups.map((g) => ({
        groupName: g.groupName,
        repositoryLocationName: repo.repositoryLocation.name,
        repositoryName: repo.repository.name,
      })),
    );
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
        fetchOptionFilters={
          <>
            {allRepos.length > 1 && <RepoFilterButton />}
            <AssetGroupSuggest
              assetGroups={assetGroups}
              value={filters.groups || []}
              onChange={(groups) => setFilters({...filters, groups})}
            />
          </>
        }
        options={{preferAssetRendering: true, explodeComposites: true}}
        explorerPath={explorerPathFromString(__GLOBAL__ + path || '/')}
        onChangeExplorerPath={onChangeExplorerPath}
        onNavigateToSourceAssetNode={onNavigateToSourceAssetNode}
      />
    </Page>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default AssetsGroupsGlobalGraphRoot;
