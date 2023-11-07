import {Page, PageHeader, Heading} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import * as React from 'react';
import {useHistory, useParams} from 'react-router-dom';

import {AssetGraphExplorer} from '../asset-graph/AssetGraphExplorer';
import {AssetGraphExplorerFilters} from '../asset-graph/AssetGraphExplorerFilters';
import {AssetGraphFetchScope} from '../asset-graph/useAssetGraphData';
import {AssetLocation} from '../asset-graph/useFindAssetLocation';
import {AssetGroupSelector} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {ReloadAllButton} from '../workspace/ReloadAllButton';
import {WorkspaceContext} from '../workspace/WorkspaceContext';

import {buildAssetGroupSelector} from './AssetGroupSuggest';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {
  globalAssetGraphPathFromString,
  globalAssetGraphPathToString,
} from './globalAssetGraphPathToString';

interface AssetGroupRootParams {
  0: string;
}

export const AssetsGroupsGlobalGraphRoot = () => {
  const {0: path} = useParams<AssetGroupRootParams>();
  const {visibleRepos} = React.useContext(WorkspaceContext);
  const history = useHistory();

  const [filters, setFilters] = useQueryPersistedState<{groups: AssetGroupSelector[]}>({
    encode: ({groups}) => ({groups: JSON.stringify(groups)}),
    decode: (qs) => ({groups: qs.groups ? JSON.parse(qs.groups) : []}),
  });

  useDocumentTitle(`Global Asset Lineage`);

  const onChangeExplorerPath = React.useCallback(
    (path: ExplorerPath, mode: 'push' | 'replace') => {
      history[mode]({
        pathname: globalAssetGraphPathToString(path),
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
        right={<ReloadAllButton label="Reload definitions" />}
      />
      <AssetGraphExplorer
        fetchOptions={fetchOptions}
        fetchOptionFilters={
          <AssetGraphExplorerFilters
            assetGroups={assetGroups}
            visibleAssetGroups={React.useMemo(() => filters.groups || [], [filters.groups])}
            setGroupFilters={React.useCallback(
              (groups) => setFilters({...filters, groups}),
              [filters, setFilters],
            )}
          />
        }
        options={{preferAssetRendering: true, explodeComposites: true}}
        explorerPath={globalAssetGraphPathFromString(path)}
        onChangeExplorerPath={onChangeExplorerPath}
        onNavigateToSourceAssetNode={onNavigateToSourceAssetNode}
      />
    </Page>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default AssetsGroupsGlobalGraphRoot;
