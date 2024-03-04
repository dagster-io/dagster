import {AssetKey} from './types';

const RECENTLY_VISITED_ASSETS_CACHE_SIZE = 10;
const RECENTLY_VISITED_ASSETS_STORAGE_KEY = 'recentlyVisitedAssets';

export function WriteAssetVisitToLocalStorage(assetKey: AssetKey) {
  if (typeof window !== 'undefined') {
    const visitedAssetsStringified = localStorage.getItem(RECENTLY_VISITED_ASSETS_STORAGE_KEY);
    const visitedAssets: AssetKey[] = visitedAssetsStringified
      ? JSON.parse(visitedAssetsStringified)
      : [];

    const assetIndex = visitedAssets.findIndex(
      (key2) => JSON.stringify(key2) === JSON.stringify(assetKey),
    );
    if (assetIndex !== -1) {
      // Remove the asset from the list
      visitedAssets.splice(assetIndex, 1);
    }

    // Add the asset to the front of the list
    visitedAssets.unshift(assetKey);

    const truncatedVisitedAssets = visitedAssets.slice(0, RECENTLY_VISITED_ASSETS_CACHE_SIZE);
    localStorage.setItem(
      RECENTLY_VISITED_ASSETS_STORAGE_KEY,
      JSON.stringify(truncatedVisitedAssets),
    );
  }
}

export function FetchRecentlyVisitedAssetsFromLocalStorage(): AssetKey[] {
  if (typeof window !== 'undefined') {
    const visitedAssetsStringified = localStorage.getItem(RECENTLY_VISITED_ASSETS_STORAGE_KEY);
    return visitedAssetsStringified ? JSON.parse(visitedAssetsStringified) : [];
  }
  return [];
}
