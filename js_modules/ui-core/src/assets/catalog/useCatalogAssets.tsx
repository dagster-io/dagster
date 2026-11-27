import {useFavoriteAssets} from '@shared/assets/useFavoriteAssets';
import {useMemo} from 'react';

import {useConnectionLocationNames} from './useConnectionLocationNames';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {useAllAssets} from '../AssetsCatalogTable';
import {filterConnectionDuplicates} from '../overview/useLinkedAsset';

/**
 * The assets the catalog lists before the asset selection is applied: scoped to favorites in
 * the favorites view, and with connection-loaded duplicates hidden unless the user opted in.
 */
export const useCatalogAssets = () => {
  const {assets, loading: assetsLoading, error} = useAllAssets();
  const {favorites, loading: favoritesLoading} = useFavoriteAssets();

  const penultimateAssets = useMemo(() => {
    if (!favorites) {
      return assets ?? [];
    }
    return (assets ?? []).filter((asset) => favorites.has(tokenForAssetKey(asset.key)));
  }, [favorites, assets]);

  const connectionLocationNames = useConnectionLocationNames();

  const [hideConnectionAssets, setHideConnectionAssets] = useStateWithStorage<boolean>(
    'dagster.hide-connection-assets',
    (v) => v ?? true,
  );

  const catalogAssets = useMemo(() => {
    if (!hideConnectionAssets || !connectionLocationNames.size) {
      return penultimateAssets;
    }

    return filterConnectionDuplicates(penultimateAssets, connectionLocationNames);
  }, [penultimateAssets, hideConnectionAssets, connectionLocationNames]);

  return {
    allAssets: assets,
    catalogAssets,
    assetsLoading,
    favorites,
    favoritesLoading,
    error,
    connectionLocationNames,
    hideConnectionAssets,
    setHideConnectionAssets,
  };
};
