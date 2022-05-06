import {useStateWithStorage} from '../hooks/useStateWithStorage';

const ASSET_VIEW_KEY = 'AssetViewPreference';

export type AssetViewType = 'flat' | 'directory' | 'graph' | 'grid';

const validateSavedAssetView = (storedValue: any) =>
  storedValue === 'flat' ||
  storedValue === 'directory' ||
  storedValue === 'graph' ||
  storedValue === 'grid'
    ? storedValue
    : 'flat';

export const useAssetView = () => {
  return useStateWithStorage<AssetViewType>(ASSET_VIEW_KEY, validateSavedAssetView);
};
