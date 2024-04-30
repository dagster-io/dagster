import {Heading, Page, PageHeader} from '@dagster-io/ui-components';
import {useCallback, useMemo} from 'react';
import {useHistory, useParams} from 'react-router-dom';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {
  globalAssetGraphPathFromString,
  globalAssetGraphPathToString,
} from './globalAssetGraphPathToString';
import {useAssetDefinitionFilterState} from './useAssetDefinitionFilterState';
import {useTrackPageView} from '../app/analytics';
import {AssetGraphExplorer} from '../asset-graph/AssetGraphExplorer';
import {AssetGraphFetchScope} from '../asset-graph/useAssetGraphData';
import {AssetLocation} from '../asset-graph/useFindAssetLocation';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {usePageLoadTrace} from '../performance';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {ReloadAllButton} from '../workspace/ReloadAllButton';

interface AssetGroupRootParams {
  0: string;
}

export const AssetsGroupsGlobalGraphRoot = () => {
  useTrackPageView();
  const {0: path} = useParams<AssetGroupRootParams>();
  const history = useHistory();

  const assetFilterState = useAssetDefinitionFilterState();

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

  const {filterFn} = assetFilterState;

  const fetchOptions = useMemo(() => {
    const options: AssetGraphFetchScope = {
      hideEdgesToNodesOutsideQuery: false,
      hideNodesMatching: (node) => !filterFn(node),
    };
    return options;
  }, [filterFn]);

  return (
    <Page style={{display: 'flex', flexDirection: 'column', paddingBottom: 0}}>
      <PageHeader
        title={<Heading>Global Asset Lineage</Heading>}
        right={<ReloadAllButton label="Reload definitions" />}
      />
      <AssetGraphExplorer
        fetchOptions={fetchOptions}
        assetFilterState={assetFilterState}
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
