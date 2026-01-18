import React, {useCallback, useMemo, useState} from 'react';
import {useHistory} from 'react-router';
import {useFavoriteAssets} from 'shared/assets/useFavoriteAssets.oss';

import {AssetGraphExplorer} from '../../asset-graph/AssetGraphExplorer';
import {AssetGraphViewType, tokenForAssetKey} from '../../asset-graph/Utils';
import {AssetLocation} from '../../asset-graph/useFindAssetLocation';
import {useOpenInNewTab} from '../../hooks/useOpenInNewTab';
import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {assetDetailsPathForKey} from '../assetDetailsPathForKey';
import {globalAssetGraphPathForGroup} from '../globalAssetGraphPathToString';

export const AssetCatalogAssetGraph = React.memo(
  ({
    selection,
    onChangeSelection,
    tabs,
  }: {
    selection: string;
    onChangeSelection: (selection: string) => void;
    tabs: React.ReactNode;
  }) => {
    const history = useHistory();
    const openInNewTab = useOpenInNewTab();

    const onNavigateToSourceAssetNode = useCallback(
      (e: Pick<React.MouseEvent<any>, 'metaKey'>, node: AssetLocation) => {
        let path;
        if (node.groupName && node.repoAddress) {
          // It is defined elsewhere, go to the global graph where it should be resolved to a full node
          path = globalAssetGraphPathForGroup(node.groupName, node.assetKey);
        } else {
          // It is not defined in another repo, just go to stub definition page
          path = assetDetailsPathForKey(node.assetKey, {view: 'definition'});
        }
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

    const fetchOptions = React.useMemo(
      () => ({
        loading: favoritesLoading,
        hideEdgesToNodesOutsideQuery,
        hideNodesMatching: favorites
          ? (node: {assetKey: {path: string[]}}) => !favorites.has(tokenForAssetKey(node.assetKey))
          : undefined,
      }),
      [hideEdgesToNodesOutsideQuery, favorites, favoritesLoading],
    );

    const lineageOptions = React.useMemo(
      () => ({preferAssetRendering: true, explodeComposites: true}),
      [],
    );

    const [opNames, setOpNames] = useState<string[]>(['']);

    return (
      <>
        {tabs}
        <AssetGraphExplorer
          fetchOptions={fetchOptions}
          options={lineageOptions}
          explorerPath={useMemo(
            () => ({
              opsQuery: selection,
              pipelineName: '',
              opNames,
            }),
            [selection, opNames],
          )}
          onChangeExplorerPath={useCallback(
            (path: ExplorerPath) => {
              setOpNames(path.opNames.length > 0 ? path.opNames : ['']);
              onChangeSelection(path.opsQuery);
            },
            [onChangeSelection],
          )}
          onNavigateToSourceAssetNode={onNavigateToSourceAssetNode}
          viewType={AssetGraphViewType.CATALOG}
          setHideEdgesToNodesOutsideQuery={setHideEdgesToNodesOutsideQuery}
        />
      </>
    );
  },
);
