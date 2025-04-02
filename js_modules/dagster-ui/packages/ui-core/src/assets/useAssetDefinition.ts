import {useContext, useMemo} from 'react';

import {ASSET_VIEW_DEFINITION_QUERY} from './AssetView';
import {useAllAssets} from './AssetsCatalogTable';
import {AssetKey} from './types';
import {AppContext} from '../app/AppContext';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {
  AssetViewDefinitionQuery,
  AssetViewDefinitionQueryVariables,
  AssetViewDefinitionQueryVersion,
} from './types/AssetView.types';
import {useIndexedDBCachedQuery} from '../search/useIndexedDBCachedQuery';

export const useAssetDefinition = (assetKey: AssetKey) => {
  const {assets} = useAllAssets();
  const cachedDefinition = useMemo(
    () =>
      assets?.find((asset) => tokenForAssetKey(asset.key) === tokenForAssetKey(assetKey))
        ?.definition,
    [assetKey, assets],
  );
  const {localCacheIdPrefix} = useContext(AppContext);
  const result = useIndexedDBCachedQuery<
    AssetViewDefinitionQuery,
    AssetViewDefinitionQueryVariables
  >({
    query: ASSET_VIEW_DEFINITION_QUERY,
    variables: {assetKey: {path: assetKey.path}},
    key: `${localCacheIdPrefix}/asset-definition-${assetKey.path.join(',')}`,
    version: AssetViewDefinitionQueryVersion,
  });

  const {assetOrError} = result.data || result.previousData || {};
  const asset = assetOrError && assetOrError.__typename === 'Asset' ? assetOrError : null;
  if (!asset) {
    return {
      definitionQueryResult: result,
      definition: null,
      lastMaterialization: null,
      cachedDefinition,
    };
  }

  return {
    definitionQueryResult: result,
    definition: asset.definition,
    lastMaterialization: asset.assetMaterializations ? asset.assetMaterializations[0] : null,
    cachedDefinition,
  };
};
