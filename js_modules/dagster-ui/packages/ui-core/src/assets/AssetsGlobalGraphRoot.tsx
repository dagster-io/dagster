import {Page} from '@dagster-io/ui-components';
import {useCallback, useMemo} from 'react';
import {useHistory, useParams} from 'react-router-dom';
import {AssetsGraphHeader} from 'shared/assets/AssetsGraphHeader.oss';
import {useFavoriteAssets} from 'shared/assets/useFavoriteAssets.oss';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {
  globalAssetGraphPathFromString,
  globalAssetGraphPathToString,
} from './globalAssetGraphPathToString';
import {useTrackPageView} from '../app/analytics';
import {AssetGraphExplorer} from '../asset-graph/AssetGraphExplorer';
import {AssetGraphViewType, tokenForAssetKey} from '../asset-graph/Utils';
import {AssetGraphFetchScope} from '../asset-graph/useAssetGraphData';
import {AssetLocation} from '../asset-graph/useFindAssetLocation';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useOpenInNewTab} from '../hooks/useOpenInNewTab';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
interface AssetGroupRootParams {
  0: string;
}

export const AssetsGlobalGraphRoot = () => {
  useTrackPageView();
  const {0: path} = useParams<AssetGroupRootParams>();
  const history = useHistory();

  useDocumentTitle(`Global Asset Lineage`);
  const openInNewTab = useOpenInNewTab();

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
    (e: Pick<React.MouseEvent<any>, 'metaKey'>, node: AssetLocation) => {
      const path = assetDetailsPathForKey(node.assetKey, {view: 'definition'});
      if (e.metaKey) {
        openInNewTab(path);
      } else {
        history.push(path);
      }
    },
    [history, openInNewTab],
  );

  const [hideEdgesToNodesOutsideQuery, setHideEdgesToNodesOutsideQuery] = useStateWithStorage(
    'hideEdgesToNodesOutsideQuery',
    (json) => {
      if (json === 'false' || json === false) {
        return false;
      }
      return true;
    },
  );

  const {favorites, loading: favoritesLoading} = useFavoriteAssets();

  const fetchOptions = useMemo(() => {
    const options: AssetGraphFetchScope = {
      hideEdgesToNodesOutsideQuery,
      hideNodesMatching: favorites
        ? (node) => !favorites.has(tokenForAssetKey(node.assetKey))
        : undefined,
      loading: favoritesLoading,
    };
    return options;
  }, [hideEdgesToNodesOutsideQuery, favorites, favoritesLoading]);

  return (
    <Page style={{display: 'flex', flexDirection: 'column', paddingBottom: 0}}>
      <AssetsGraphHeader />

      <AssetGraphExplorer
        fetchOptions={fetchOptions}
        options={{preferAssetRendering: true, explodeComposites: true}}
        explorerPath={globalAssetGraphPathFromString(path)}
        onChangeExplorerPath={onChangeExplorerPath}
        onNavigateToSourceAssetNode={onNavigateToSourceAssetNode}
        viewType={AssetGraphViewType.GLOBAL}
        setHideEdgesToNodesOutsideQuery={setHideEdgesToNodesOutsideQuery}
      />
    </Page>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default AssetsGlobalGraphRoot;
