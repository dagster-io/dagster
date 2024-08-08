import {Icon} from '@dagster-io/ui-components';
import {useState} from 'react';
import {getVisibleFeatureFlagRows} from 'shared/app/getVisibleFeatureFlagRows.oss';

import {useFeatureFlags} from './Flags';
import {TopNavButton} from './TopNavButton';
import {UserSettingsDialog} from './UserSettingsDialog/UserSettingsDialog';

export const UserSettingsButton = () => {
  const {flagSettingsPage} = useFeatureFlags();
  const [isOpen, setIsOpen] = useState(false);

  if (flagSettingsPage) {
    return null;
  }

  return (
    <>
      <TopNavButton onClick={() => setIsOpen(true)} title="User settings">
        <Icon name="settings" size={20} />
      </TopNavButton>
      <UserSettingsDialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        visibleFlags={getVisibleFeatureFlagRows()}
      />
    </>
  );
};
