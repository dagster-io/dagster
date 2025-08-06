import {useStateWithStorage} from '../../hooks/useStateWithStorage';

const SHOW_ASSETS_WITHOUT_DEFINITIONS_STORAGE_KEY = 'showAssetsWithoutDefinitions';

export const useShowAssetsWithoutDefinitions = () => {
  const [showAssetsWithoutDefinitions, setShowAssetsWithoutDefinitions] = useStateWithStorage(
    SHOW_ASSETS_WITHOUT_DEFINITIONS_STORAGE_KEY,
    (value: any) => (typeof value === 'boolean' ? value : false),
  );

  return {showAssetsWithoutDefinitions, setShowAssetsWithoutDefinitions};
};
