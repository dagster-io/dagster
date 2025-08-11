import {useStateWithStorage} from '../../hooks/useStateWithStorage';

const SHOW_STUB_ASSETS_STORAGE_KEY = 'showStubAssets';

export const useShowStubAssets = () => {
  const [showStubAssets, setShowStubAssets] = useStateWithStorage(
    SHOW_STUB_ASSETS_STORAGE_KEY,
    (value: any) => (typeof value === 'boolean' ? value : false),
  );

  return {showStubAssets, setShowStubAssets};
};
