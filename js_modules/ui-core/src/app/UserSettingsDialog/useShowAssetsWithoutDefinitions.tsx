import {useUserSettingDefaults} from '@shared/app/UserSettingsDialog/useUserSettingDefaults';

import {useStateWithStorage} from '../../hooks/useStateWithStorage';

const SHOW_ASSETS_WITHOUT_DEFINITIONS_STORAGE_KEY = 'showAssetsWithoutDefinitions';

export const useShowAssetsWithoutDefinitions = () => {
  const {showAssetsWithoutDefinitions: defaultShowAssetsWithoutDefinitions} =
    useUserSettingDefaults();
  const [showAssetsWithoutDefinitions, setShowAssetsWithoutDefinitions] = useStateWithStorage(
    SHOW_ASSETS_WITHOUT_DEFINITIONS_STORAGE_KEY,
    (value: any) => (typeof value === 'boolean' ? value : defaultShowAssetsWithoutDefinitions),
  );

  return {showAssetsWithoutDefinitions, setShowAssetsWithoutDefinitions};
};
