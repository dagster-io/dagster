import {Heading, Page, PageHeader} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import {useCallback, useContext, useMemo} from 'react';
import {useHistory, useParams} from 'react-router-dom';

import {buildAssetGroupSelector} from './AssetGroupSuggest';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {
  globalAssetGraphPathFromString,
  globalAssetGraphPathToString,
} from './globalAssetGraphPathToString';
import {AssetGraphExplorer} from '../asset-graph/AssetGraphExplorer';
import {AssetGraphFetchScope} from '../asset-graph/useAssetGraphData';
import {AssetLocation} from '../asset-graph/useFindAssetLocation';
import {AssetGroupSelector, ChangeReason} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {usePageLoadTrace} from '../performance';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {ReloadAllButton} from '../workspace/ReloadAllButton';
import {WorkspaceContext} from '../workspace/WorkspaceContext';

interface AssetGroupRootParams {
  0: string;
}

export const AssetsGroupsGlobalGraphRoot = () => {
  const {0: path} = useParams<AssetGroupRootParams>();
  const {visibleRepos} = useContext(WorkspaceContext);
  const history = useHistory();

  const [filters, setFilters] = useQueryPersistedState<{
    groups?: AssetGroupSelector[];
    computeKindTags?: string[];
    changedInBranch?: ChangeReason[];
  }>({
    encode: ({groups, computeKindTags, changedInBranch}) => ({
      groups: groups?.length ? JSON.stringify(groups) : undefined,
      computeKindTags: computeKindTags?.length ? JSON.stringify(computeKindTags) : undefined,
      changedInBranch: changedInBranch?.length ? JSON.stringify(changedInBranch) : undefined,
    }),
    decode: (qs) => ({
      groups: qs.groups ? JSON.parse(qs.groups) : [],
      computeKindTags: qs.computeKindTags ? JSON.parse(qs.computeKindTags) : [],
      changedInBranch: qs.changedInBranch ? JSON.parse(qs.changedInBranch) : [],
    }),
  });

  useDocumentTitle(`Global Asset Lineage`);
  const trace = usePageLoadTrace('GlobalAssetGraph');

  const onChangeExplorerPath = useCallback(
    (path: ExplorerPath, mode: 'push' | 'replace') => {
      history[mode]({
        pathname: globalAssetGraphPathToString(path),
        search: history.location.search,
      });
    },
    [history],
  );

  const onNavigateToSourceAssetNode = useCallback(
    (node: AssetLocation) => {
      history.push(assetDetailsPathForKey(node.assetKey, {view: 'definition'}));
    },
    [history],
  );

  const fetchOptions = useMemo(() => {
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

        if (filters.changedInBranch?.length) {
          if (node.changedReasons.find((reason) => filters.changedInBranch!.includes(reason))) {
            return false;
          }
          return true;
        }

        return false;
      },
    };
    return options;
  }, [filters, visibleRepos]);

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
