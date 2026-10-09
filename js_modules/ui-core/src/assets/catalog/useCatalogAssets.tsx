import {useFavoriteAssets} from '@shared/assets/useFavoriteAssets';
import {useContext, useMemo} from 'react';

import {useConnectionLocationNames} from './useConnectionLocationNames';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {WorkspaceContext} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {useAllAssets} from '../AssetsCatalogTable';
import {filterAssetsByCodeLocation} from '../filterAssetsByCodeLocation';
import {filterConnectionDuplicates} from '../overview/useLinkedAsset';

/**
 * The assets the catalog lists before the asset selection is applied: scoped to favorites in
 * the favorites view and to the selected code location, and with connection-loaded duplicates
 * hidden unless the user opted in.
 */
export const useCatalogAssets = () => {
  const {assets, loading: assetsLoading, error} = useAllAssets();
  const {favorites, loading: favoritesLoading} = useFavoriteAssets();

  const {codeLocationFilter} = useContext(WorkspaceContext);

  const penultimateAssets = useMemo(() => {
    const inLocation = filterAssetsByCodeLocation(assets ?? [], codeLocationFilter);
    if (!favorites) {
      return inLocation;
    }
    return inLocation.filter((asset) => favorites.has(tokenForAssetKey(asset.key)));
  }, [favorites, assets, codeLocationFilter]);

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
