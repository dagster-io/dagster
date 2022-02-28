import {useStateWithStorage} from '../hooks/useStateWithStorage';

const ASSET_VIEW_KEY = 'AssetViewPreference';

type View = 'flat' | 'directory' | 'graph';

const validateSavedAssetView = (storedValue: any) =>
  storedValue === 'flat' || storedValue === 'directory' || storedValue === 'graph'
    ? storedValue
    : 'flat';

export const useAssetView = () => {
  return useStateWithStorage<View>(ASSET_VIEW_KEY, validateSavedAssetView);
};
