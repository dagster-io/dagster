import {Icon} from '@dagster-io/ui-components';
import {useState} from 'react';
import {useVisibleFeatureFlagRows} from 'shared/app/useVisibleFeatureFlagRows.oss';

import {useFeatureFlags} from './Flags';
import {TopNavButton} from './TopNavButton';
import {UserSettingsDialog} from './UserSettingsDialog/UserSettingsDialog';

export const UserSettingsButton = () => {
  const {flagSettingsPage} = useFeatureFlags();
  const [isOpen, setIsOpen] = useState(false);

  const visibleFlags = useVisibleFeatureFlagRows();

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
        visibleFlags={visibleFlags}
      />
    </>
  );
};
