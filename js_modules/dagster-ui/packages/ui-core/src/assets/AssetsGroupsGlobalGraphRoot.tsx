import {Page, PageHeader, Heading} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import * as React from 'react';
import {useHistory, useParams} from 'react-router-dom';

import {AssetGraphExplorer} from '../asset-graph/AssetGraphExplorer';
import {AssetGraphFetchScope} from '../asset-graph/useAssetGraphData';
import {AssetLocation} from '../asset-graph/useFindAssetLocation';
import {AssetGroupSelector} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useStartTrace} from '../performance';
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

  const [filters, setFilters] = useQueryPersistedState<{
    groups: AssetGroupSelector[];
    computeKindTags: string[];
  }>({
    encode: ({groups, computeKindTags}) => ({
      groups: groups.length ? JSON.stringify(groups) : undefined,
      computeKindTags: computeKindTags.length ? JSON.stringify(computeKindTags) : undefined,
    }),
    decode: (qs) => ({
      groups: qs.groups ? JSON.parse(qs.groups) : [],
      computeKindTags: qs.computeKindTags ? JSON.parse(qs.computeKindTags) : [],
    }),
  });

  useDocumentTitle(`Global Asset Lineage`);
  const trace = useStartTrace('GlobalAssetGraph');

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

  return (
    <Page style={{display: 'flex', flexDirection: 'column', paddingBottom: 0}}>
      <PageHeader
        title={<Heading>Global Asset Lineage</Heading>}
        right={<ReloadAllButton label="Reload definitions" />}
      />
      <AssetGraphExplorer
        fetchOptions={fetchOptions}
        filters={filters}
        setFilters={setFilters}
        options={{preferAssetRendering: true, explodeComposites: true}}
        explorerPath={globalAssetGraphPathFromString(path)}
        onChangeExplorerPath={onChangeExplorerPath}
        onNavigateToSourceAssetNode={onNavigateToSourceAssetNode}
        isGlobalGraph
        trace={trace}
      />
    </Page>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default AssetsGroupsGlobalGraphRoot;
